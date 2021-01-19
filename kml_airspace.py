import json
import datetime
import argparse
import os
import zipfile
import tempfile
from pykml.factory import KML_ElementMaker as KML
from lxml import etree

# pip install pykml

def coord2str(coord):
    return ','.join([str(x) for x in coord])


def coords2str(coords):
    return ' '.join([coord2str(c) for c in coords])


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


def add_airspace_styles(doc):
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/red_triangle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            KML.PolyStyle(
                KML.color('994444ff'),
            ),
            KML.LineStyle(
                KML.color('ff4444ff'),
            ),
            id='ESOS',
        ))
    doc.Document.append(KML.Style(
            KML.IconStyle(
                KML.scale(0.5),
                KML.Icon(
                    KML.href("icons/blue_triangle.png"),
                    KML.hotSpot(x="0.5", y="0.5", xunits="fraction", yunits="fraction")
                ),
            ),
            KML.PolyStyle(
                KML.color('99ffcc33'),
            ),
            KML.LineStyle(
                KML.color('ffffcc33'),
            ),
            id='ESMM',
        ))


def pm_point(point, style):
    return KML.Placemark(
        KML.name(point['name']),
        KML.visibility(1),
        KML.styleUrl(style),
        KML.Point(
            KML.coordinates(coord2str([
                point['lon'], point['lat']
            ])),
        ))


def pm_points(points, style):
    pts_folder = KML.Folder(
        KML.name('Points'),
        KML.visibility(1))

    for p in points:
        pts_folder.append(pm_point(p, style));
    
    return pts_folder


def pm_volume(vol, style):
    lower = []
    upper = []
    sides = []
    min_alt = vol['min_alt'] * 0.3048
    max_alt = vol['max_alt'] * 0.3048
    coords = vol['coordinates']
    x1=0
    y1=0
    for i, c in enumerate(coords[:-1]):
        x0 = c['lon']
        y0 = c['lat']
        lower.append([x0, y0, min_alt])
        upper.append([x0, y0, max_alt])
        n = coords[i+1]
        x1 = n['lon']
        y1 = n['lat']
        sides.append([[x0,y0,min_alt], [x0,y0,max_alt], [x1,y1,max_alt], [x1,y1,min_alt], [x0,y0,min_alt]])
    lower.append([x1, y1, min_alt])
    upper.append([x1, y1, max_alt])

    mg = KML.MultiGeometry()

    p = KML.Polygon()
    p.append(KML.altitudeMode('absolute'))
    p.append(KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coords2str(lower)))))
    mg.append(p)

    p = KML.Polygon()
    p.append(KML.altitudeMode('absolute'))
    p.append(KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coords2str(upper)))))
    mg.append(p)

    for s in sides:
        p = KML.Polygon()
        p.append(KML.altitudeMode('absolute'))
        p.append(KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coords2str(s)))))
        mg.append(p)
    
    return KML.Placemark(mg, KML.styleUrl(style))

def pm_sector(sector, style):
    sec_folder = KML.Folder(
        KML.name(sector['name']),
        KML.visibility(1))

    for vol in sector['volumes']:
        sec_folder.append(pm_volume(vol, style))
    
    return sec_folder

def pm_sectors(sectors, style):
    secs_folder = KML.Folder(
        KML.name('Sectors'),
        KML.visibility(1))

    for s in sectors:
        secs_folder.append(pm_sector(s, style))
    
    return secs_folder

def kml_airspase(data):
    doc = KML.kml(KML.Document())
    add_airspace_styles(doc)
    for asp in data:
        name = asp['name']
        asp_folder = KML.Folder(
            KML.name(name),
            KML.visibility(1),
            id='CENTRE_{}'.format(asp['centre_id']))
        asp_folder.append(pm_points(asp['points'], '#{}'.format(name)))
        asp_folder.append(pm_sectors(asp['sectors'], '#{}'.format(name)))
        doc.Document.append(asp_folder)
    return doc


def save_kmz(kml_data, out_file):
    with tempfile.NamedTemporaryFile() as tf:
        et = etree.ElementTree(kml_data)
        et.write(tf, pretty_print=True)
        tf.flush()

        with zipfile.ZipFile(out_file, mode='w') as zip:
            zip.write(tf.name, 'doc.kml')
            zip.write('icons/blue_triangle.png')
            zip.write('icons/red_triangle.png')


def read_file(in_file, out_file):
    print("Reading JSON file", in_file)
    with open(in_file, 'r') as jf:
        json_data = json.load(jf, object_hook=datetime_parser)
        kml_data =  kml_airspase(json_data)
        save_kmz(kml_data, out_file)


def read_archive(in_file, out_file):
    with zipfile.ZipFile(in_file, mode='r') as zip:
        with zip.open('airspace.json') as jf:
            json_data = json.load(jf, object_hook=datetime_parser)
            kml_data =  kml_airspase(json_data)
            save_kmz(kml_data, out_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LFV ATC Data: Airspace to KML')
    parser.add_argument('-i', '--input', required=False, help='Input airspace.json or zip containing that file')
    parser.add_argument('-o', '--output', required=True, help='Output kmz file')
    args = parser.parse_args()

    ext = os.path.splitext(args.input)[1].lower()
    
    if ext == '.json':
        read_file(args.input, args.output)
    elif ext == '.zip':
        read_archive(args.input, args.output)
    else:
        print("Unknown file extension '{}'".format(ext))
