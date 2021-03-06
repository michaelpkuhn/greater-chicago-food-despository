import json


def main(d_ls):
    '''
    Puts zip and county data into separate lists
    Sends data to merge() and writes to merged json
    Returns jsons in list

    input:
        d_ls (list): list of dictionaries
            dictionary format:
            {geo_area:{geo_code:{metrics...},...}}
    output:
        final_json_ls (list): list of dictionaries
            len() = 2 (default, county and zip)
    '''
    # unpack d_ls into dictionary by geo_area
    d_dict = {}
    for d in d_ls:
        d_key = str(list(d.keys())[0])
        d_values = list(d.values())[0]
        if d_key not in d_dict:
            d_dict[d_key] = [d_values]
        else:
            d_dict[d_key].append(d_values)

    final_json_ls = []
    # breakpoint()
    # calls merge function on each geo_area
    geo_dict = {'zip': 'zipcodes', 'county': 'counties'}
    for k, v in d_dict.items():
        geo_str = geo_dict[k]
        fp = 'shape_files/ILgeojson.json' if geo_str != 'counties' \
             else 'tests/resources/ILgeojson_county.json'
        # only add bins to geojson properties
        geo_json, g_map = get_geojson(fp=fp, param=geo_str)
        # breakpoint()
        merged_json = merge(v)
        final_json = {}
        final_json[geo_str] = merge_geojson(geo_json, g_map, merged_json)
        final_json_ls.append(final_json)
        # breakpoint()
        with open(F'final_jsons/merged{k}_output.json', 'w') as f:
            json.dump(final_json, f, separators=(',', ':'))

    # saves merged_dict to file
    with open('final_jsons/merged_output.json', 'w') as f:
        # geojson = getGeoJson()
        merged_dict = {k: v for d in final_json_ls for k, v in d.items()}
        # breakpoint()
        json.dump(merged_dict, f, separators=(',', ':'))

    return merged_dict


def merge(dict_list=list()):
    '''
    Merges data dictionaries
    input: list of geo data dictionaries (list)
            dictionary format {geo_area:{'geo_code':{'metric1':1,...},...}}
            within each dictionary assumes all geo-areas
            include the same metrics
    output: merged geo data dictionary, same format
    '''
    # TODO What happens if some geo areas do not have all the data elements?
    # Error handled: prints geo area not in list index
    # Do we want to add the missing data with null values?
    # breakpoint()
    merged_dict = dict()

    # Get all the geocodes in both datasets
    merged_keys = set()
    for d in dict_list:
        # breakpoint()
        merged_keys.update(set(d.keys()))

    # loop through all geocodes
    for k in merged_keys:
        # creates geocode key for mergedDict
        merged_dict[k] = dict()
        for i, d in enumerate(dict_list):
            # breakpoint()
            # if the geocode is not in the dictionary,
            # print to console and continue
            # TODO add missing geocode metric here?
            try:
                value = list(d[k])
            except KeyError:
                print(k, F' not in dictList[{i}]')
                continue
            for v in value:
                # if the metric is already in the dictionary it is a duplicate
                if v in merged_dict[k]:
                    # if the duplicate key includes an identical value continue
                    if merged_dict[k][v] == d[k][v]:
                        continue
                    # Otherwise, raise exception and return metric name
                    e = 'Duplicate metric key: rename to avoid overwrite'
                    raise Exception(e, v)
                # The metric is not in the dictionary, add it
                else:
                    merged_dict[k][v] = d[k][v]
    return merged_dict


def get_geojson(fp='shape_files/ILgeojson.json', param=""):
    '''
    Loads geojson file and gets param if specified
    Returns dictionary and index map of geocodes in GeoJSON features list
    '''
    # geojson file from https://github.com/OpenDataDE/State-zip-code-GeoJSON
    # ZCTA updated in 2010, further updates, if any, would be posted here
    # https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html # noqa: E501
    # Create a merged county and zip geojson and name ILgeojson.json
    # this code currently assumes we are only looking at zips and counties
    g_ls = []
    with open(fp) as f:
        j = json.load(f)
        j = j.get(param, j)

    if param == "":
        g_ls.append(j['counties'])
        g_ls.append(j['zipcodes'])
    else:
        g_ls.append(j)

    g_map = {}
    for g in g_ls:
        for i, f in enumerate(g['features']):
            f_props = f['properties']
            try:
                geocode = f_props['ZCTA']
            except KeyError:
                geocode = f_props['STATE'] + f_props['COUNTY']
            g_map[geocode] = i
    return j, g_map


def merge_geojson(geo_json, g_map, merged_json, inplace=False):
    '''
    Adds data to GeoJSON properties by geocode
    Input:
        geo_json (dict):  GeoJSON
        g_map (dict): maps geo-area to geo_json index
        merged_json (dict): merged json of geo-data
        inplace (bool): if true, returns the modified original
    Output:
        geo_json (dict): geo-json merged with merged_json values
    '''
    # creates new geo_json by default to avoid unintended side effects
    if inplace is False:
        geo_json = dict(geo_json)
    for g in merged_json:
        g_index = g_map[g]
        geo_json['features'][g_index]['properties'].update(merged_json[g])
    return geo_json


def flatten_geojson(fp='final_jsons/mergedcounty_output.json'):
    '''
    Removes nested properties from GeoJSON for GIS visualization
    Does not check for duplicates keys, may overwrite data: use unique keys
    '''
    with open(fp) as f:
        j = json.load(f)

    for geo_area in j:
        features = j[geo_area]['features']
        for i, f in enumerate(features):
            new_props = {}
            for prop, value in f['properties'].items():
                if type(value) == dict:
                    new_props.update(value)
                else:
                    new_props[prop] = value
            features[i]['properties'] = new_props

    with open('_flattened.'.join(fp.split('.')), 'w') as f:
        json.dump(j, f)
    return j


if __name__ == '__main__':
    main()
