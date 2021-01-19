import json
import datetime
import os
import zipfile
import argparse
import csv

def datetime_parser(dct):
    for k, v in dct.items():
        if type(v) is str:
            try:
                dct[k] = datetime.datetime.strptime(v[0:26], "%Y-%m-%dT%H:%M:%S.%f")
                #dct[k] = dateutil.parser.parse(v)
            except:
                try:
                    dct[k] = datetime.datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")
                except:
                    pass
    return dct

def analyse_flight(data):
    id = data['id']

    fpl_base = data['fpl']['fpl_base']
    adar = None
    adep = None
    ades = None
    callsign = None
    aircraft_type = None
    wtc = None
    for x in fpl_base:
        if x['adar'] is not None:
            adar = x['adar']
        if x['adep'] is not None:
            adep = x['adep']
        if x['ades'] is not None:
            ades = x['ades']
        if x['callsign'] is not None:
            callsign = x['callsign']
        if x['aircraft_type'] is not None:
            aircraft_type = x['aircraft_type']
        if x['wtc'] is not None:
            wtc = x['wtc']
    
    plots = data['plots']
    plot_count = len(plots)
    if plot_count == 0:
        print("Warning, flight {} has empty plots".format(id))
        plots_start = None
        plots_end = None
    else:
        plots_start = plots[0]['time_of_track']
        plots_end = plots[-1]['time_of_track']

    return {
        'id': id,
        'callsign': callsign,
        'adar': adar,
        'adep': adep,
        'ades': ades,
        'aircraft_type': aircraft_type,
        'wtc': wtc,
        'plots_start': plots_start,
        'plots_end': plots_end,
        'plot_count': plot_count
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LFV ATC Data: Index archive')
    parser.add_argument('-a', '--archive', required=True)
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()

    print("Indexing archive '{}'".format(args.archive))

    idx = []
    with zipfile.ZipFile(args.archive, 'r') as zip_file:
        tot = len(zip_file.infolist())-2
        i = 0
        for zi in zip_file.infolist():
            bn = os.path.basename(zi.filename)
            
            if bn[0] >= '0' and bn[0] <= '9':
                i += 1
                if i % 1000 == 0:
                    print("  processed {} of {} flights".format(i, tot))
                with zip_file.open(zi.filename) as df:
                    data = json.load(df, object_hook=datetime_parser)
                idx.append(analyse_flight(data))
            

    with open(args.output, 'w', newline='') as csvfile:
        fieldnames = ['id', 'callsign', 'adep', 'ades', 'adar', 'aircraft_type', 'wtc', 'plots_start', 'plots_end', 'plot_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in idx:
            writer.writerow(i)
        
    print("Done!")
    