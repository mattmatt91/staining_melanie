from array import array
from operator import index
from PIL import Image
from pathlib import Path
import numpy as np
from os import scandir, path
import pandas as pd
from pathlib import Path
from time import time
from datetime import datetime


def scan_folder(path_data):
    subfolders = [ f.path for f in scandir(path_data) if f.is_dir() ]
    folder_dict = {}

    for folder in subfolders:
        if folder.find('result') < 0:
            path_dict = {'neuron': folder + '\\neuron.tif', 'protein': folder +  '\\protein.tif'}
            name = folder[folder.rfind('\\')+1:]
            folder_dict[name] = path_dict
    return folder_dict


def read_files(path_dict):
    crop_props = (20, 20, 500, 500)
    # cropping
    # dict_tifs = {'neuron': Image.open(path_dict['neuron']).crop((crop_props)), 'protein': Image.open(path_dict['protein']).crop(crop_props)}
    # emtire tif
    dict_tifs = {'neuron': Image.open(path_dict['neuron']), 'protein': Image.open(path_dict['protein'])}
    return dict_tifs


def normalize(array):
    maximum = 65535
    minimum = 0
    return (((array-minimum)/(maximum-minimum))*255).astype(int)


def to_array_raw(dict_tifs):
    dict_array = {}
    for i in dict_tifs:
        dict_array[i] = normalize(np.array(dict_tifs[i]))
    return dict_array

def to_array(dict_tifs):
    dict_array = {}
    for i in dict_tifs:
        dict_array[i] = np.array(dict_tifs[i])
    return dict_array


def rgb_tifs(dict_tifs, dict_colors):  
    dict_colored_tifs = {}
    for i in dict_tifs:
        color_index = dict_colors[i]
        array = np.array(dict_tifs[i])
        if np.max(array)>= 256:
            bw = normalize(array)
        else:
            bw = array
        len_x = len(bw)
        len_y = len(bw[0])
        rgb = np.zeros((len_x, len_y, 3), dtype=np.uint8)
        rgb[:,:,color_index] = bw
        img = Image.fromarray(rgb, 'RGB')
        # img.show()
        dict_colored_tifs[i] = img
    return dict_colored_tifs


def to_bw(array):
    # array = array.astype(np.uint8)
    image = Image.fromarray(array)
    # image.show()
    return image


def to_tif(array):
    array = array.astype(np.uint8)
    image = Image.fromarray(array, 'RGB')
    # image.show()
    return image


def sum_arrays(dict_arrays):
    arrays = [dict_arrays[i] for i in dict_arrays]
    sum = np.sum(arrays, axis=0)
    return sum


def show_tifs(dict_tifs):
    for i in dict_tifs:
        dict_tifs[i].show()


    
    

def compare(dict_arrays, dict_thresholds):
    counter_com = 0
    counter_neuron = 0
    threshold_neuron = dict_thresholds['neuron']
    threshold_protein = dict_thresholds['protein']

    protein = dict_arrays['protein']
    neuron = dict_arrays['neuron']

    df_protein = pd.DataFrame(protein)
    df_neuron = pd.DataFrame(neuron)

    array_compare = np.empty(dict_arrays['protein'].shape)
    for row_protein, row_neuron, r in zip(protein, neuron, range(len(neuron))):
        for col_protein, col_neuron, c in zip(row_protein, row_neuron, range(len(row_neuron))):
            if col_neuron >= threshold_neuron:
                counter_neuron += 1
            if col_protein >= threshold_protein and col_neuron >= threshold_neuron:
                counter_com += 1
                array_compare[r][c] = (col_protein+col_neuron)//2
            else:
                array_compare[r][c] = 0
        
    return array_compare, counter_com, counter_neuron
    
    
def print_dict(dict):
    for i in dict:
        data = dict[i]
        print('name is {0}'.format(i))
        print('type is {0}'.format(type(data)))
        try:
            print('size is {0}'.format(data.size))
        except:
            pass
        try:
            print('shape is {0}'.format(data.shape))
            print('max is {0}'.format(np.max(data)))
            print('dtype is {0}'.format(data.dtype))
            
        except:
            pass
        print('\n')


def print_array(data):
    print('type is {0}'.format(type(data)))
    print('shape is {0}'.format(data.shape))
    print('max is {0}'.format(np.max(data)))
    print('\n')

def save_tif(tif, path_data, name, current_time):
    path_results = path.join(path_data, "results"+ current_time)
    path_results = Path(path_results)
    path_results.mkdir(parents=True, exist_ok=True)
    name = name + '.tif'
    path_tif = path.join(path_results, name)
    print(path_tif)
    tif.save(path_tif, compression='raw')


def save_result(list_result, dict_thresholds,current_time, path):
    df_result= pd.DataFrame(list_result)

    print(df_result)
    path_results = path.join(path_data, "results"+current_time)
    path_results = Path(path_results)
    path_results.mkdir(parents=True, exist_ok=True)
    file_name = 'th_pro' + str(dict_thresholds['protein']) + '_th_neu' + str(dict_thresholds['neuron']) + 'results.txt'
    path_csv = path.join(path_results, file_name)
    df_result.to_csv(path_csv, sep='\t', index=False)


def main(path_data, dict_thresholds, dict_colors):
    print(path_data)
    now = datetime.now()
    current_time = now.strftime("%H_%M_%S")
    start = time()
    path_dict = scan_folder(path_data)
    list_result = []

    for i in path_dict:
        start = time()
        try:
            print('reading {0}...'.format(i))
            dict_tifs = read_files(path_dict[i])
            dict_arrays = to_array_raw(dict_tifs)
            comparison, overlap_counts, neuron_counts = compare(dict_arrays, dict_thresholds)
            this_result = {'name': i, 'counts_neuron': neuron_counts, 'counts_overlap': overlap_counts, 'ratio': overlap_counts/neuron_counts}
            list_result.append(this_result)
            print(this_result)
            tif_compare = to_bw(comparison)
            dict_arrays['compare'] = comparison
            print_dict(dict_arrays)
            dict_tifs['compare'] = tif_compare
            
            # print_dict(dict_tifs)
            dict_rgb_tifs = rgb_tifs(dict_tifs, dict_colors)
            print_dict(dict_rgb_tifs)
            #print_dict(dict_rgb_tifs)
            dict_rgb_array = to_array(dict_rgb_tifs)
            print_dict(dict_rgb_array)
            # print_dict(dict_rgb_array)
            summed_array = sum_arrays(dict_rgb_array)
            # print(summed_array.shape)
            # print('summed array: {0}'.format(summed_array.shape))
            summed_tif = to_tif(summed_array)
            # print('summed tif: {0}'.format(summed_tif.size))

            # summed_tif.show()
            save_tif(summed_tif, path_data, i, current_time)
            
        except Exception as e:
            print('error while reading ',i)
            print(e)
        print('duration for tif ', i, ': ', time()-start, '\n')
    save_result(list_result, dict_thresholds,current_time, path)

dict_thresholds = {'neuron': 30,'protein': 15} # colors have values from 0 to 2550
#path_data = 'C:\\Users\\Matthias\\Desktop\\GitHub\\staining_melanie\data'
path_data = 'C:\\Users\\Matthias\\Desktop\\GitHub\\staining_melanie\\data_small'
dict_colors = {'neuron':1, 'protein':0, 'compare':2}

if __name__ == "__main__":
    main(path_data, dict_thresholds, dict_colors)