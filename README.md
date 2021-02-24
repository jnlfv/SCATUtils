# SCAT Dataset Utils

## Indexing flights
The script *idx_flight.py* creates an index of all flights in an zip archive. The index is stored in CSV format with one line per flight containing *id, callsign	adep, ades, adar, aircraft_type, wtc, plots_start, plots_end* and *plot_count*.

To run the script Python 3 is requred. The script takes two arguments, the name of the zip archive and the name of the output file. 

**Example usage:**
```
python idx_flights.py -a ~/lfv_atc_data/data20161015_20161021.zip -o /tmp/idx.csv
```

## Convert flight to KML
The script *kml_flight.py* creates KML files from JSON flight objects that can be viewed in Google Earth. The JSON files can either be read from a folder or read directly from the zip archive. Formally the output of the script is KMZ files, which are compressed KML files.

To run the script Python 3 and pyKML are requred. The package pyKML can be installed using pip:
```
pip install pykml
```

To run the script at least the output directory must be specified using '-o' or '--out-path' as well as at least one flight file. When reading from an unzipped folders, wildcard characters can be used to convert multiple files. Optionally the flight files can be read from an zipped archive that may be specified using '-a' or '--archive'. In this case whildcard characters may not be used.

**Example usage:**
```
python kml_flight.py -a ~/lfv_atc_data/data20161015_20161021.zip -o /tmp/kml/ 100010.json 100999.json
```
The above command will read the files 100010.json and 100999.json from the archive data20161015_20161021.zip and write the files 100010.kmz and 100999.kmz in the folder /tmp/kml.


```
python kml_flight.py -o /tmp/kml/ ~/lfv_atc_data/data20161015_20161021/10001*.json
```
The above command will read the ten files 100010.json to 100019.json from the archive data20161015_20161021.zip and write the files 100010.kmz to 100019.kmz in the folder /tmp/kml.

## Convert Airspace to KML
The script *kml_airspace.py* creates a KML file from JSON airspace file that can be viewed in Google Earth. The JSON file can either be read from a folder or read directly from the zip archive. Formally the output of the script is a KMZ file, which is a compressed KML files.

To run the script Python 3 and pyKML are requred. The package pyKML can be installed using pip:
```
pip install pykml
```

To run the script the input file and output file must be specified. The input is specified using '-i' or '--input' followed by a file name. The outoput is specified using '-o' or '--output' followed by the name of the output file. If the input file is a zip file it is assumed that the name of the airspace file in the archive is 'airspace.json'.

**Example usage:**
```
python kml_airspace.py -i ~/lfv_atc_data/data20161015_20161021.zip -o /tmp/airspace.kmz
```
The above command will read the file airspace.json from the archive data20161015_20161021.zip and write the file airspace.kmz to the folder /tmp/kml.

```
python kml_airspace.py -i ~/lfv_atc_data/data20161015_20161021/airspace.json -o /tmp/airspace.kmz
```
The above command will read the file airspace.json from the directory ~/fv_atc_data/data20161015_20161021 and write the file airspace.kmz to the folder /tmp/kml.
