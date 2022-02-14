from operator import index
from PIL import Image
from pathlib import Path
import numpy as np
from os import scandir, path
import pandas as pd
from pathlib import Path
from time import time
from datetime import datetime


def read_files(path_dict):
    crop_props = (20, 20, 500, 500)
    # cropping
    dict_tifs = {'neuron': Image.open(path_dict['neuron']).crop((crop_props)), 'protein': Image.open(path_dict['protein']).crop(crop_props)}
    # emtire tif
    # dict_tifs = {'neuron': Image.open(path_dict['neuron']), 'protein': Image.open(path_dict['protein'])}
    return dict_tifs


def normalize(array, maximum):
    minimum = 0
    return (((array-minimum)/(maximum-minimum))*255).astype(int)


def to_array(dict_tifs, dict_max):
    neuron = normalize(np.array(dict_tifs['neuron']), dict_max['neuron'])
    protein = normalize(np.array(dict_tifs['protein']), dict_max['protein'])
    dict_array = {'neuron':neuron, 'protein':protein}
    return dict_array


def color_tif(tif):
    im_rgb = Image.new("RGBA", tif.size)
    im_rgb.paste(tif)

                
def array_sum(dict_arrays):
    array_sum = dict_arrays['neuron'] + dict_arrays['protein']  + dict_arrays['overlap']
    return array_sum


def show_tif(tif):
        tif.show()
    

def to_tif(array):
    image = Image.fromarray(array)
    # image.show()
    return image


def compare(dict_arrays, dict_thresholds):
    counter_com = 0
    counter_neuron = 0
    array_compare = np.empty(dict_arrays['protein'].shape)
    threshold_neuron = dict_thresholds['neuron']
    threshold_protein = dict_thresholds['protein']
    protein = dict_arrays['protein']
    neuron = dict_arrays['neuron']
    for row_protein, row_neuron, r in zip(protein, neuron, range(len(neuron))):
        for col_protein, col_neuron, c in zip(row_protein, row_neuron, range(len(row_neuron))):
            if col_neuron >= threshold_neuron:
                counter_neuron += 1
            if col_protein >= threshold_protein and col_neuron >= threshold_neuron:
                counter_com += 1
                array_compare[r][c] = 255
            else:
                array_compare[r][c] = 0
        
    return counter_com, array_compare, counter_neuron


def scan_folder(path_data):
    subfolders = [ f.path for f in scandir(path_data) if f.is_dir() ]
    folder_dict = {}

    for folder in subfolders:
        if folder.find('result') < 0:
            path_dict = {'neuron': folder + '\\neuron.tif', 'protein': folder +  '\\protein.tif'}
            name = folder[folder.rfind('\\')+1:]
            folder_dict[name] = path_dict
    return folder_dict


def color_arrays(dict_tifs, dict_colors):  
    dict_colored_arrays = {}
    
    for i in dict_tifs: 
        this_tif = to_tif(dict_tifs[i])
        im_rgb = Image.new("RGBA", this_tif.size)
        im_rgb.paste(this_tif)
        dict_colored_arrays[i] = im_rgb

    dict_colored_arrays = {'neuron': np.array(dict_colored_arrays['neuron']),
                           'protein': np.array(dict_colored_arrays['protein']),
                            'overlap': np.array(dict_colored_arrays['overlap'])}

    new_dict_colored_arrays = {}
    for array, color in zip(dict_colored_arrays,dict_colors):
        counter = 0
        new_array = dict_colored_arrays[array]
        for row in range(len(dict_colored_arrays[array])):
            for col in range(len(dict_colored_arrays[array])):
                new_array[row][col] = dict_colored_arrays[array][row][col]*np.array(dict_colors[color])
                counter += 1
        # to_tif(new_array).show()

        new_dict_colored_arrays[array] = new_array
    return new_dict_colored_arrays


def save_tif(tif, path_data, name, current_time):
    path_results = path.join(path_data, "results"+ current_time)
    path_results = Path(path_results)
    path_results.mkdir(parents=True, exist_ok=True)
    name = name + '.tif'
    path_tif = path.join(path_results, name)
    print(path_tif)
    tif.save(path_tif, compression='raw')


def get_max(path_dict):
    max_protein = 0
    max_neuron = 0
    for i in path_dict:
        dict_tifs = {'neuron': Image.open(path_dict[i]['neuron']), 'protein': Image.open(path_dict[i]['protein'])}
        this_max_neuron = np.max(np.array(dict_tifs['neuron']))
        this_max_protein = np.max(np.array(dict_tifs['protein']))
        if this_max_neuron >= max_neuron:
            max_neuron = this_max_neuron
        if this_max_protein >= max_protein:
            max_protein = this_max_protein

    dict_max = {'neuron':max_neuron, 'protein': max_protein}
    return dict_max



def main(path_data, dict_thresholds, dict_colors):

    print(path_data)
    now = datetime.now()
    current_time = now.strftime("%H_%M_%S")
    start = time()
    path_dict = scan_folder(path_data)
    list_result = []

    print('looking for global max...')
    dict_max = get_max(path_dict)
    print(dict_max)
    print('duration {0}...'.format(time()-start))

    for i in path_dict:
        start = time()
        try:
            print('reading {0}...'.format(i))
            dict_tifs = read_files(path_dict[i])
            dict_arrays = to_array(dict_tifs, dict_max)
            print('duration {0}...'.format(time()-start))

            print('comparing {0}...'.format(i))
            camparison, array_compare, counter_neuron = compare(dict_arrays, dict_thresholds)
            dict_arrays['overlap'] = array_compare
            this_df_result = {'sample': i, 'compare': camparison, 'neuron':counter_neuron, 'ratio': (camparison/(counter_neuron+1))*100} 
            print(this_df_result)
            print(i, ' total counts: ',camparison)
            print('duration {0}...'.format(time()-start))

            print('coloring {0}...'.format(i))
            colored_arrays = color_arrays(dict_arrays, dict_colors)
            print('duration {0}...'.format(time()-start))

            print('summing arrays {0}...'.format(i))
            sum_array = array_sum(colored_arrays)
            print('duration {0}...'.format(time()-start))

            tif_sum = to_tif(sum_array)
            save_tif(tif_sum, path_data, i, current_time)
            # show_tif(tif_sum)

            list_result.append(this_df_result)
        except Exception as e:
            print('error while reading ',i)
            print(e)
        print('duration for tif ', i, ': ', time()-start, '\n')
        

    df_result= pd.DataFrame(list_result)

    print(df_result)
    path_results = path.join(path_data, "results"+current_time)
    path_results = Path(path_results)
    path_results.mkdir(parents=True, exist_ok=True)
    file_name = 'th_pro' + str([dict_thresholds['protein']]) + '_th_neu' + str([dict_thresholds['neuron']]) + 'results.txt'
    path_csv = path.join(path_results, file_name)
    df_result.to_csv(path_csv, sep='\t', index=False)
        



dict_thresholds = {'neuron': 30,'protein': 40} # colors have values from 0 to 2550
#path_data = 'C:\\Users\\Matthias\\Desktop\\GitHub\\staining_melanie\data'
path_data = 'C:\\Users\\Matthias\\Desktop\\GitHub\\staining_melanie\\data_small'
dict_colors = {'neuron':[1, 0, 0, 1], 'protein':[0, 1, 0, 1], 'overlap':[0, 0, 1, 1]}

if __name__ == "__main__":
    main(path_data, dict_thresholds, dict_colors)


