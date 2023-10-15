import easyocr
import numpy as np
import PIL
from PIL import Image, ImageDraw
import cv2
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
import re
import pandas as pd

import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

st.set_page_config(layout='wide')

st.title('BizCardx: Extracting Business Card Data with OCR')



#tabs

tab1, tab2 = st.tabs(["Data Extraction", "Data modification"])

with tab1:
   st.subheader("Data Extraction")

   uploaded_file = st.file_uploader("Select the Business Card",type =['png','jpg', "jpeg"], accept_multiple_files=False)


   if uploaded_file is not None:
        reader=easyocr.Reader(['en'],gpu=True)
    
        image=Image.open(uploaded_file)

        image_array=np.array(image)
        text_read=reader.readtext(image_array)

        result=[]

        for text in text_read:
            result.append(text[1])

   col1, col2= st.columns(2)

   with col1:
            
            try:
                # Define a funtion to draw the box on image
                def draw_boxes(image, text_read, color='blue', width=2):

                    # Create a new image with bounding boxes
                    image_with_boxes = image.copy()
                    draw = ImageDraw.Draw(image_with_boxes)
                    
                    # draw boundaries
                    for bound in text_read:
                        p0, p1, p2, p3 = bound[0]
                        draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width)
                    return image_with_boxes

                # Function calling
                result_image = draw_boxes(image, text_read)

                # Result image
                st.image(result_image, caption='Captured text from the card')

            except NameError:
                 #st.write('Upload the Image')  
                 pass 

   with col2:
            
            try:
            
                data={
                    'Company':[],
                    'Name':[],
                    'Designation':[],
                    'Contact_number':[],
                    'Email':[],
                    'Website':[],
                    'Area':[],
                    'District':[],
                    'State':[],
                    'Pincode':[]
                }

                def get_data(info):
                    district=""
                    for details, i in enumerate(info):
                            if "www " in i.lower() or "www." in i.lower():
                                data['Website'].append(i)
                            elif 'WWW' in i:
                                data["Website"].append(info[details] + "." + info[details-1])

                        # email
                            elif '@' in i:
                                data['Email'].append(i)

                            # Mobile Number
                            elif '-' in i:
                                data['Contact_number'].append(i)
                                if len(data['Contact_number'])==2:
                                    data['Contact_number']='&'.join(data['Contact_number'])

                            #  Card holder
                            elif details ==0:
                                data['Name'].append(i)

                            # Designation
                            elif details ==1:
                                data['Designation'].append(i)

                            # To get COMPANY NAME
                            if details == len(info)-1:
                              data["Company"].append(i)
                            elif re.findall("^[GBFIs].*", i):
                              data["Company"].append(i)
                               
                       
                            if len(data["Company"])>2:
                                for k in range (len(data["Company"])-1):
                                    if len(data["Company"][k])>12 :
                                      data["Company"].pop(k)
                                      
                                    else:  
                                    #elif len(data["Company"][2])<5 :
                                      #data["Company"].pop(2) 
                                      #data["Company"].append(data["Company"][0]+" "+data["Company"][1])
                                     # data["Company"].append(ab)
                                     pass

                            if len(data["Company"])>=2:
                              try:
                                #data["Company"] = "  ".join(data["Company"])
                               # ab=(data["Company"][0]+" "+data["Company"][1])
                                data["Company"].pop(2)
                                #data["Company"].append(ab)
                                data["Company"] = "  ".join(data["Company"]) 
                              except:
                                data["Company"] = "  ".join(data["Company"])         

                                     

                                        

                            # area
                            if re.findall('^[0-9] [a-zA-Z]+',i):
                                data['Area'].append(i.split(",")[0])
                            elif re.findall("[0-9] [a-zA-Z]+", i):
                                data["Area"].append(i.split(",")[0]) 

                            #District
            
                            match1 = re.findall(".+St , ([a-zA-Z]+).+", i)
                            match2 = re.findall(".+St,, ([a-zA-Z]+).+", i)
                            match3 = re.findall("^[E].*", i)
                            if match1:
                                district = match1[0]  # Assign the matched city value
                            elif match2:
                                district = match2[0]  # Assign the matched city value
                            elif match3:
                                district = match3[0]  # Assign the matched city value

                            # To get STATE
                            state_match = re.findall("[a-zA-Z]{9} +[0-9]", i)
                            if state_match:
                                data["State"].append(i[:9])
                            elif re.findall("^[0-9].+, ([a-zA-Z]+);", i):
                                data["State"].append(i.split()[-1])
                            if len(data["State"]) == 2:
                                data["State"].pop(0)

                            # To get PINCODE
                            if len(i) >= 6 and i.isdigit():
                                data["Pincode"].append(i)
                            elif re.findall("[a-zA-Z]{9} +[0-9]", i):
                                data["Pincode"].append(i[10:])

                    data["District"].append(district)  # Append the city value to the 'city' array
                    
                    

                    #if len(data)["Company"]>2:


                # Call funtion
                get_data(result)

                # Create dataframe
                data_df = pd.DataFrame(data)

                st.write(data)
                st.dataframe(data_df)

            except NameError:
                st.write('Upload the Image')