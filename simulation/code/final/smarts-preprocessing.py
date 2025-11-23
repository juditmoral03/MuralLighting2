import pandas as pd
import numpy as np

SMART_FILES = ["pedret-d1t1.ext.txt", "pedret-d1t2.ext.txt", "pedret-d1t3.ext.txt",
               "pedret-d2t1.ext.txt", "pedret-d2t2.ext.txt", "pedret-d2t3.ext.txt",
               "pedret-d3t1.ext.txt", "pedret-d3t2.ext.txt", "pedret-d3t3.ext.txt"]


print("Processing SMART_FILES...")

for file in SMART_FILES:
    moment = file.split('.')[0][-4:]
    print("--- "+str(moment))

    df = pd.read_csv('emitters/SMARTS-spectras/'+file, sep='\s+')

    #GLOBAL
    file_csv = 'emitters/csv/'+moment+'-global.csv'
    file_spd = 'emitters/spd/'+moment+'-global.spd'

    df_selected = df[['Wvlgth', 'Global_horizn_irradiance']]
    df_selected.to_csv(file_csv, index=False)

    df_new = pd.read_csv(file_csv, delimiter=',')    
    with open(file_spd, 'w') as file:
        for index, row in df_new.iterrows():
            file.write(f"{row['Wvlgth']} {row['Global_horizn_irradiance']/(2*np.pi)}\n")    

    #DIFFUSE
    file_csv = 'emitters/csv/'+moment+'-sky.csv'
    file_spd = 'emitters/spd/'+moment+'-sky.spd'

    df_selected = df[['Wvlgth', 'Difuse_horizn_irradiance']]
    df_selected.to_csv(file_csv, index=False)

    df_new = pd.read_csv(file_csv, delimiter=',')    
    with open(file_spd, 'w') as file:
        for index, row in df_new.iterrows():
            file.write(f"{row['Wvlgth']} {row['Difuse_horizn_irradiance']/(2*np.pi)}\n")

    ##DIRECT
    file_csv = 'emitters/csv/'+moment+'-sun.csv'
    file_spd = 'emitters/spd/'+moment+'-sun.spd'

    df_selected = df[['Wvlgth', 'Direct_normal_irradiance']]
    df_selected.to_csv(file_csv, index=False)

    df_new = pd.read_csv(file_csv, delimiter=',')    
    with open(file_spd, 'w') as file:
        for index, row in df_new.iterrows():
            file.write(f"{row['Wvlgth']} {row['Direct_normal_irradiance']}\n")

print("FINISHED!")