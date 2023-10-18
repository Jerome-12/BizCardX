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
                                data["Website"].append(info[details-1] + "." + info[details])

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
                            elif details == len(info) - 1:
                                data["Company"].append(i)      

                            # area
                            if re.findall('^[0-9] [a-zA-Z]+',i):
                                data['Area'].append(i)
                            elif re.findall("[0-9] [a-zA-Z]+", i):
                                data["Area"].append(i) 

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
                        # if len(data["State"]) == 2:
                            #    data["State"].pop(0)

                            # To get PINCODE
                            if len(i) >= 6 and i.isdigit():
                                data["Pincode"].append(i)
                            elif re.findall("[a-zA-Z]{9} +[0-9]", i):
                                data["Pincode"].append(i[10:])

                    data["District"].append(district)  # Append the city value to the 'city' array

                # Call funtion
                get_data(result)

                # Create dataframe
                data_df = pd.DataFrame(data)

                #st.write('data')
                st.dataframe(data_df)

            except NameError:
                st.write('Upload the Image')


        # Upload button

            class SessionState:
                def __init__(self, **kwargs):
                  self.__dict__.update(kwargs)
            session_state = SessionState(data_uploaded=False)
   
            Upload = st.button('**Upload to MySQL DB**', key='upload_button')

                # Check if the button is clicked
            if Upload:
                    session_state.data_uploaded = True

                # Execute the program if the button is clicked
            if session_state.data_uploaded:
                    # Connect to the MySQL server
                    connect = mysql.connector.connect(
                        host="localhost",
                        user="root",
                        password=os.getenv("MYSQLKEY"),
                        auth_plugin='mysql_native_password')

                    # Create a new database and use it
                    mycursor = connect.cursor()
                    mycursor.execute("CREATE DATABASE IF NOT EXISTS Bizcard")
                    mycursor.close()
                    connect.database = "Bizcard"

                    # Connect to the newly created database
                    engine = create_engine(os.getenv("MYSQLSRC"), echo=False)

                    try:
                        # Use pandas to insert the DataFrame data into the SQL Database table
                        data_df.to_sql('bizcardx', engine, if_exists='append', index=False, dtype={
                            "Company": sqlalchemy.types.VARCHAR(length=225),
                            "Name": sqlalchemy.types.VARCHAR(length=225),
                            "Designation": sqlalchemy.types.VARCHAR(length=225),
                            "Contact_number": sqlalchemy.types.String(length=50),
                            "Email": sqlalchemy.types.TEXT,
                            "Website": sqlalchemy.types.TEXT,
                            "Area": sqlalchemy.types.VARCHAR(length=225),
                            "City": sqlalchemy.types.VARCHAR(length=225),
                            "State": sqlalchemy.types.VARCHAR(length=225),
                            "Pincode": sqlalchemy.types.String(length=10)})
                        
                        #Uploaded completed message
                        st.info('Data Successfully Uploaded')

                    except:
                        st.info("Card data already exists")

                    connect.close()

                    # Reset the session state after executing the program
                    session_state.data_uploaded = False

            else:
                #st.info('Click the Browse file button and upload an image')
                 pass

                                            

                             
                                  
                               
            

with tab2:
    st.subheader('Data Modification')   

    col1,col2=st.columns(2)

    with col1:
            st.subheader(':violet[Edit option]')

        #try:
            # Connect to the database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password=os.getenv("MYSQLKEY"),
                auth_plugin='mysql_native_password',
                database="Bizcard")

            cursor = conn.cursor()

            # Execute the query to retrieve the cardholder data
            cursor.execute("SELECT Name FROM bizcardx")

            # Fetch all the rows from the result
            rows = cursor.fetchall()

            # Take the cardholder name
            names = []
            for row in rows:
                names.append(row[0])

            # Create a selection box to select cardholder name
            Name_select = st.selectbox("**Select a Name to Edit the details**", names, key='Name_select')

            # Collect all data depending on the cardholder's name
            cursor.execute( "SELECT Company, Name, Designation, Contact_number, Email, Website, Area, District, State, Pincode FROM bizcardx WHERE Name=%s", (Name_select,))
            col_data = cursor.fetchone()

            # DISPLAYING ALL THE INFORMATION
            Company = st.text_input("Company", col_data[0])
            Name = st.text_input("Name", col_data[1])
            Designation = st.text_input("Designation", col_data[2])
            Contact_number = st.text_input("Contact number", col_data[3])
            Email = st.text_input("Email", col_data[4])
            Website = st.text_input("Website", col_data[5])
            Area = st.text_input("Area", col_data[6])
            District = st.text_input("District", col_data[7])
            State = st.text_input("State", col_data[8])
            Pincode = st.text_input("Pincode", col_data[9]) 

            # Create a session state object
            class SessionState:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
            session_state = SessionState(data_update=False)
            
            # Update button
            #st.write('Click the Update button to update the modified data')
            update = st.button('**Update**', key = 'update')

            # Check if the button is clicked
            if update:
                session_state.data_update = True

            # Execute the program if the button is clicked
            if session_state.data_update:

                # Update the information for the selected business card in the database
                cursor.execute(
                    "UPDATE bizcardx SET Company = %s, Designation = %s, Contact_number = %s, Email = %s, "
                    "Website = %s, Area = %s, District = %s, State = %s, Pincode = %s "
                    "WHERE Name=%s",
                    (Company, Designation, Contact_number, Email, Website, Area, District, State, Pincode, Name))
                
                conn.commit()

                st.success("successfully Updated.")

                # Close the database connection
                conn.close()
                
                session_state.data_update = False

        #except:
            #st.info('No data stored in the database')

    # --------------------------------------   /   /   Delete option   /   /   -------------------------------------- #

    with col2:
        st.subheader(':violet[Delete option]')

        try:
            # Connect to the database
            conn_del = mysql.connector.connect(
                host="localhost",
                user="root",
                password=os.getenv("MYSQLKEY"),
                auth_plugin='mysql_native_password',
                database="Bizcard")

            # Execute the query to retrieve the cardholder data
            cursor = conn_del.cursor()
            cursor.execute("SELECT Name FROM bizcardx")

            # Fetch all the rows from the result
            del_name = cursor.fetchall()

            # Take the cardholder name
            del_names = []
            for row in del_name:
                del_names.append(row[0])

            # Create a selection box to select cardholder name
            delete_name = st.selectbox("**Select a Name to Delete the details**", del_names, key='delete_name')

            # Create a session state object
            class SessionState:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
            session_state = SessionState(data_delet=False)

            # Delet button
            #st.write('Click the Delete button to Delete selected Name details')
            delet = st.button('**Delete**', key = 'delet')

            # Check if the button is clicked
            if delet:
                session_state.data_delet = True

            # Execute the program if the button is clicked
            if session_state.data_delet:
                cursor.execute(f"DELETE FROM bizcardx WHERE Name='{delete_name}'")
                conn_del.commit()
                st.success("Successfully deleted from database.")

                # Close the database connection
                conn_del.close()

                session_state.data_delet = False

        except:
            st.info('No data stored in the database')
