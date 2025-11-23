import pandas as pd


def create_spd_file(sheet_name, position, filepath= 'data/IT1072.xlsx'):
    intensity_column = f'Unnamed: {position}'

    df = pd.read_excel(filepath, sheet_name=sheet_name, usecols=['Longitud de onda (nm)', intensity_column])
    

    print(df.head(10))
    df = df.drop(df.index[0])
    print(df.head(10))
    output_filename = f"spdFiles/XII/{sheet_name}_position{position}.spd"

    with open(output_filename, 'w') as file:
        for index, row in df.iterrows():
            # Ensure the correct intensity column is referenced in the f-string
            file.write(f"{row['Longitud de onda (nm)']} {row[intensity_column]}\n")

create_spd_file('Abeja_Horizontal', 2)
create_spd_file('Abeja_Horizontal', 6)
create_spd_file('Aceite_Horizontal', 6)
create_spd_file('Aceite_sal_Horizontal', 6)
create_spd_file('Aceite_sal_Horizontal', 2)
create_spd_file('Parafina_diam3_Horizontal', 3)
create_spd_file('Parafina_diam3_Horizontal', 2)
create_spd_file('Parafina_diam3_Horizontal', 6)
create_spd_file('Parafina_diam8_Horizontal', 6)


#CODE--------------------------------------------------------------------------------------
#create_spd_file(sheet_name='Parafina_diam3_Horizontal', position=2)  

excel_file_path =  'data/IT1072.xlsx'
xls = pd.ExcelFile(excel_file_path)

# Get the list of all sheet names
sheet_names = xls.sheet_names
print(sheet_names)


##################################################################################3
#print columns of excel fille

# df = pd.read_excel(excel_file_path, sheet_name='Parafina_diam8_Horizontal')
# column_names = df.columns.tolist()
# print(column_names)

# for column in df.columns:
#     print(f"Column: {column}")
#     print(df[column])  # Print column content without the index
#     print()