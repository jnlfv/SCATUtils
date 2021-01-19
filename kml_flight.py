import json
import datetime
import argparse
import os
import zipfile
from pykml.factory import KML_ElementMaker as KML
from lxml import etree

# pip install pykml

def coord2str(coord):
    return ','.join([str(x) for x in coord])

def coords2str(coords):
    return ' '.join([coord2str(c) for c in coords])

def pm_plots(plots, fid):
    pm = KML.Placemark(KML.visibility(1))
    pm.append(KML.name("plots"))
    pm.append(KML.styleUrl('#radar_track'))

    coords = []
    for p in plots:
        lat = p["I062/105"]["lat"]
        lon = p["I062/105"]["lon"]
        if "I062/136" in p:
            alt = p["I062/136"]["measured_flight_level"]*30.48
        else:
            alt = 0
        coords.append((lon, lat, alt))
    ls = KML.LineString(
            KML.extrude(1),
            KML.altitudeMode('absolute'),
            KML.coordinates(coords2str(coords))
    )
    pm.append(ls)
    return pm

def pm_fpl(flight):
    label = {
        'fpl_arr': 'arr',
        'fpl_base': 'base',
        'fpl_dep': 'dep',
        'fpl_clearance': 'clr',
        'fpl_plan_update': 'upd',
        'fpl_holding': 'hold',
    }
    vis = 0
    fpl_events = []
    for k, v in flight["fpl"].items():
        for x in v:
            fpl_events.append(
                {
                    "type": k,
                    "data": x
                }
            )
    
    fpl_events.sort(key=lambda x:x["data"]["time_stamp"])
    idx = 0
    plots = flight["plots"]
    for f in fpl_events:
        while idx<len(plots)-1:
            p = plots[idx]
            if p["time_of_track"] >= f["data"]["time_stamp"]:
                break
            idx+=1
        p = plots[idx]
        f["lat"] = p["I062/105"]["lat"]
        f["lon"] = p["I062/105"]["lon"]
        if "I062/136" in p:
            f["alt"] = p["I062/136"]["measured_flight_level"]*30.48
        else:
            f["alt"] = 0
    folder = KML.Folder(KML.name('fpl'), KML.visibility(vis))
    for f in fpl_events:
        desc = f['type']
        for k in sorted(f['data'].keys()):
            desc += '\n{}: {}'.format(k, f['data'][k])
        pm = KML.Placemark(
            KML.visibility(vis),
            KML.name(label[f["type"]]),
            KML.description(desc),
            KML.Point(
                KML.coordinates(coord2str([
                    f['lon'], f['lat'], f['alt']
                ])),
                KML.altitudeMode('absolute')
            ))
        pm.append(KML.styleUrl('#{}'.format(f["type"])))
        folder.append(pm)
    return folder

def pm_fix(fix):
    vis = 0
    route = fix["route"]
    ts = fix["time_stamp"]
    folder = KML.Folder(KML.name(ts.strftime("%Y:%m:%dT%H:%M:%s.%f")), KML.visibility(vis))
    coords = []
    for rp in route:
        desc = ''
        for k in sorted(rp.keys()):
            desc += '{}: {}\n'.format(k, rp[k])
        pm = KML.Placemark(
            KML.visibility(vis),
            KML.name(rp["fix_name"]),
            KML.description(desc),
            KML.Point(
                KML.coordinates(coord2str([
                    rp['lon'], rp['lat'], rp['afl_value']*30.48
                ])),
                KML.altitudeMode('absolute'),
            ))
        pm.append(KML.styleUrl('#tp_point'))
        folder.append(pm)
        coords.append((rp['lon'], rp['lat'], rp['afl_value']*30.48))
    ls = KML.LineString(
            KML.extrude(1),
            KML.altitudeMode('absolute'),
            KML.coordinates(coords2str(coords))
    )
    pm = KML.Placemark(KML.visibility(vis), KML.name('trajectory'))
    pm.append(KML.name("trajectory"))
    pm.append(ls)
    pm.append(KML.styleUrl('#tp_track'))
    folder.append(pm)
    return folder


def pm_fixes(flight):
    vis = 0
    folder = KML.Folder(KML.name('predicted_trajectory'), KML.visibility(vis))
    for tp in flight["predicted_trajectory"]:
        folder.append(pm_fix(tp))
    return folder


def datetime_parser(dct):
    for k, v in dct.items():
        if type(v) is str:
            try:
                if len(v) > 26:
                    v = v[0:26] #python datetime only supports microseconds
                dct[k] = datetime.datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%f")
            except:
                try:
                    dct[k] = datetime.datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")
                except:
                    pass
    return dct

def add_flight_styles(doc):
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/blue_circle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            id='fpl_dep',
        ))
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/yellow_circle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            id='fpl_arr',
        ))
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/green_circle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            id='fpl_clearance',
        ))
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/magenta_circle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            id='fpl_base',
        ))
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/turquoise_circle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            id='fpl_plan_update',
        ))
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/red_circle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            id='fpl_holding',
        ))
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/pink_dimond.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            id='tp_point',
        ))

    doc.Document.append(KML.Style(
            KML.PolyStyle(
                KML.color('9900ffff'),
            ),
            KML.LineStyle(
                KML.color('ff00ffff'),
            ),
            id='radar_track',
        ))
    doc.Document.append(KML.Style(
            KML.PolyStyle(
                KML.color('992299ff'),
            ),
            KML.LineStyle(
                KML.color('ff2299ff'),
            ),
            id='tp_track',
        ))


def kml_flight(flight):
    doc = KML.kml(KML.Document())
    add_flight_styles(doc)
    fid = flight["id"]
    flt = KML.Folder(KML.name(str(fid)))
    doc.Document.append(flt)
    flt.append(pm_plots(flight["plots"], fid))
    flt.append(pm_fpl(flight))
    flt.append(pm_fixes(flight))
    return doc


def save_file(kml_data, file_name, out_path):
    kml_file_name = os.path.splitext(os.path.basename(file_name))[0] + '.kml'
    out_file = os.path.join(out_path, kml_file_name)
    print("Writing KML to", out_file)
    with open(out_file, 'wb') as kf:
        et = etree.ElementTree(kml_data)
        et.write(kf, pretty_print=True)
    return out_file

def save_kmz(kml_data, file_name, out_path):
    tmp_file = save_file(kml_data, file_name, out_path)
    kmz_file_name = os.path.splitext(os.path.basename(file_name))[0] + '.kmz'
    out_file = os.path.join(out_path, kmz_file_name)
    with zipfile.ZipFile(out_file, mode='w') as zip:
        zip.write(tmp_file, 'doc.kml')
        zip.write('icons/blue_circle.png')
        zip.write('icons/green_circle.png')
        zip.write('icons/magenta_circle.png')
        zip.write('icons/pink_dimond.png')
        zip.write('icons/red_circle.png')
        zip.write('icons/turquoise_circle.png')
        zip.write('icons/yellow_circle.png')
    os.remove(tmp_file)

def read_files(files, out_path):
    for f in files:
        print("Reading JSON file", f)
        with open(f, 'r') as jf:
            json_data = json.load(jf, object_hook=datetime_parser)
            kml_data =  kml_flight(json_data)
            save_kmz(kml_data, f, out_path)


def read_archive(archive, files, out_path):
    with zipfile.ZipFile(archive, mode='r') as zip:
        for f in files:
            with zip.open(f) as jf:
                json_data = json.load(jf, object_hook=datetime_parser)
                kml_data =  kml_flight(json_data)
                save_kmz(kml_data, f, out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LFV ATC Data: Flight to KML')
    parser.add_argument('-a', '--archive', required=False)
    parser.add_argument('-o', '--out-path', required=True)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    if args.archive is None:
        read_files(args.files, args.out_path)
    else:
        read_archive(args.archive, args.files, args.out_path)
