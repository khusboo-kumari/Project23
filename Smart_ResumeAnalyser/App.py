import streamlit as st
import pandas as pd
import base64
import random
import time
import datetime
import webbrowser
import os
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io
import random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import pafy
import plotly.express as px


def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(csv.encode()).decode()
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(
        resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider(
        'Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


connection = pymysql.connect(
    host='localhost', user='root', password='', db='sra')
cursor = connection.cursor()


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    DB_table_name = 'user_details'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp, str(
        no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="Smart Resume Analyzer",
    # page_icon='./Logo/SRA_Logo.ico',
    page_icon='./Logo/ats-software-resume.png',

)


def run():
    st.title("Smart Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin", "Create Resume"]
    choice = st.sidebar.selectbox(
        "Choose among the given options:", activities)
    img = Image.open('./Logo/ats-software-resume.png')

    img = img.resize((250, 250))
    st.image(img)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)

    # Create table
    DB_table_name = 'user_details'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Uploading your Resume....'):
                time.sleep(4)
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                # Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''', unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''', unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''', unsafe_allow_html=True)

                st.subheader("**Skills Recommendation💡**")
                # Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='1')

                # recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch',
                              'machine learning', 'deep Learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = [
                    'android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development',
                               'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes', 'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro', 'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp', 'user research', 'user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                # Courses recommendation
                for i in resume_data['skills']:
                    # Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success(
                            "** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling', 'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras', 'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask", 'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    # Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success(
                            "** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel',
                                              'Magento', 'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    # Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success(
                            "** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter',
                                              'Kotlin', 'XML', 'Java', 'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    # IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success(
                            "** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation', 'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    # Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success(
                            "** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq', 'Prototyping', 'Wireframes', 'Storyframes',
                                              'Adobe Photoshop', 'Editing', 'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe', 'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System', value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''', unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                #
                # Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(
                    ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(
                    ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)

                # Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score+20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''', unsafe_allow_html=True)

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration✍/h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''', unsafe_allow_html=True)

                if 'Hobbies' or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''', unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''', unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''', unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **")
                st.balloons()

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                            str(resume_data['no_of_pages']), reco_field, cand_level, str(
                                resume_data['skills']),
                            str(recommended_skills), str(rec_course))

                # Resume writing video
                # st.header("**Bonus Video for Resume Writing Tips💡**")
                # resume_vid = random.choice(resume_videos)
                # res_vid_title = fetch_yt_video(resume_vid)
                # st.subheader("✅ **"+res_vid_title+"**")
                # st.video(resume_vid)

                # # Interview Preparation Video
                # st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
                # interview_vid = random.choice(interview_videos)
                # int_vid_title = fetch_yt_video(interview_vid)
                # st.subheader("✅ **" + int_vid_title + "**")
                # st.video(interview_vid)

                connection.commit()
            else:
                st.error('Something went wrong..')

    elif choice == 'Create Resume':
        f = open('GFG.html', 'w')

        # the html code which will go in the file GFG.html
        html_template = """
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <title>Resume Page</title>
                <meta name="description" content="">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <!-- custom css -->
                <link rel="stylesheet" href="assets/css/main.css">
            </head>
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');

            :root{
                --clr-blue: #1A91F0;
                --clr-blue-mid: #1170CD;
                --clr-blue-dark: #1A1C6A;
                --clr-white: #fff;
                --clr-bright: #EFF2F9;
                --clr-dark: #1e2532;
                --clr-black: #000;
                --clr-grey: #656e83;
                --clr-green: #084C41;
                --font-poppins: 'Poppins', sans-serif;
                --font-manrope: 'Manrope', sans-serif;;
                --transition: all 300ms ease-in-out;
            }

            *{
                padding: 0;
                margin: 0;
                box-sizing: border-box;
            }

            html{
                font-size: 10px;
            }

            body{
                font-size: 1.6rem;
                font-family: var(--font-poppins);
            }

            button{
                border: none;
                background-color: transparent;
                outline: 0;
                cursor: pointer;
                font-family: inherit;
            }

            img{
                width: 100%;
                display: block;
            }

            a{
                text-decoration: none;
            }

            /* fonts */
            .font-poppins{font-family: var(--font-poppins);}
            .font-manrope{font-family: var(--font-manrope);}

            /* text colors */
            .text-blue{color: var(--clr-blue);}
            .text-blue-mid{color: var(--clr-blue-mid);}
            .text-blue-dark{color: var(--clr-blue-dark);}
            .text-bright{color: var(--clr-bright);}
            .text-dark{color: var(--clr-dark);}
            .text-grey{color: var(--clr-grey);}
            .text-white{color: var(--clr-white);}

            /* backgrounds */
            .bg-blue{background-color: var(--clr-blue);}
            .bg-blue-mid{background-color: var(--clr-blue-mid);}
            .bg-blue-dark{background-color: var(--clr-blue-dark);}
            .bg-bright{background-color: var(--clr-bright);}
            .bg-dark{background-color: var(--clr-dark);}
            .bg-grey{background-color: var(--clr-grey);}
            .bg-white{background-color: var(--clr-white);}
            .bg-black{background-color: var(--clr-black);}
            .bg-green{background-color: var(--clr-green);}

            .text-center{ text-align: center;}
            .text-left{text-align: left;}
            .text-right{text-align: right;}
            .text-uppercase{text-transform: uppercase;}
            .text-lowercase{text-transform: lowercase;}
            .text-capitalize{text-transform: capitalize;}
            .text{
                color: var(--clr-dark);
                opacity: 0.9;
                margin: 2rem 0;
                line-height: 1.6;
            }

            .fw-2{font-weight: 200;}
            .fw-3{font-weight: 300;}
            .fw-4{font-weight: 400;}
            .fw-5{font-weight: 500;}
            .fw-6{font-weight: 600;}
            .fw-7{font-weight: 700;}
            .fw-8{font-weight: 800;}

            .fs-13{font-size: 13px;}
            .fs-14{font-size: 14px;}
            .fs-15{font-size: 15px;}
            .fs-16{font-size: 16px;}
            .fs-17{font-size: 17px;}
            .fs-18{font-size: 18px;}
            .fs-19{font-size: 19px;}
            .fs-20{font-size: 20px;}
            .fs-21{font-size: 21px;}
            .fs-22{font-size: 22px;}
            .fs-23{font-size: 23px;}
            .fs-24{font-size: 24px;}
            .fs-25{font-size: 25px;}

            .ls-1{letter-spacing: 1px;}
            .ls-2{letter-spacing: 2px;}

            .container{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 1.6rem;
            }

            /* bars button */
            .bars{
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 16.5px;
                width: 25px;
            }
            .bars .bar{
                width: 100%;
                height: 2px;
                background-color: var(--clr-blue);
                transition: var(--transition);
            }

            .bars:hover .bar{
                background-color: var(--clr-dark);
            }

            /* buttons */
            .btn{
                font-size: 14.5px;
                font-weight: 600;
                padding: 1.4rem 1.6rem;
                border-radius: 4px;
                display: inline-block;
            }

            .btn-primary{
                background-color: var(--clr-blue);
                color: var(--clr-white);
                border: 1px solid var(--clr-blue);
                transition: var(--transition);
            }

            .btn-primary:hover{
                background-color: transparent;
                color: var(--clr-dark);
                border-color: var(--clr-grey);
            }

            .btn-secondary{
                background-color: transparent;
                color: var(--clr-dark);
                border: 1px solid var(--clr-grey);
                transition: var(--transition);
            }

            .btn-secondary:hover{
                background-color: var(--clr-blue);
                color: var(--clr-white);
                border-color: var(--clr-blue);
            }

            .btn-group button:first-child, .btn-group a:first-child{
                margin-right: 1rem!important;
            }

            /* navbar part */
            .navbar{
                height: 80px;
                display: flex;
                align-items: center;
                box-shadow: rgba(0, 0, 0, 0.08) 0px 3px 8px;
            }

            .navbar .container{
                width: 100%;
            }

            .navbar-brand{
                display: flex;
                align-items: center;
                justify-content: flex-start;
                font-size: 1.8rem;
            }
            .navbar-brand-text{
                color: var(--clr-dark);
                font-weight: 600;
            }
            .navbar-brand-text span{
                color: var(--clr-blue);
            }
            .navbar-brand-icon{
                width: 25px;
                margin-right: 6px;
                opacity: 0.8;
            }
            .brand-and-toggler{
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .header{
                min-height: calc(100vh - 80px);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            .header-content{
                max-width: 740px;
                margin-right: auto;
                margin-left: auto;
            }
            .header-content img{
                max-width: 760px;
                border-top-right-radius: 8px;
                border-top-left-radius: 8px;
                margin-top: 3.2rem;
            }
            .lg-title{
                margin: 1.4rem 0;
                font-size: 37px;
                line-height: 1.4;
                color: var(--clr-dark);
            }
            .header-content p{
                margin-bottom: 2.6rem;
                line-height: 1.6;
            }


            /* section one */
            .section-one{
                padding: 64px 0;
                min-height: 80vh;
                display: flex;
                align-items: center;
            }
            .section-one-l img{
                max-width: 545px;
                margin-right: auto;
                margin-left: auto;
            }
            .section-one-r{
                margin-top: 4rem;
            }

            .section-one .btn-group{
                margin-top: 2rem;
            }
            .section-one-r{
                max-width: 545px;
                margin-right: auto;
                margin-left: auto;
            }
            .section-one-r .btn-group{
                margin-top: 3rem;
            }

            /* section two */
            .section-two{
                padding: 64px 0;
            }
            .section-two .section-items{
                display: grid;
                gap: 2rem;
            }

            .section-two .section-item{
                max-width: 350px;
                text-align: center;
                margin-right: auto;
                margin-left: auto;
            }
            .section-two .section-item-icon{
                margin: 1rem 0;
            }
            .section-two .section-item-icon img{
                width: 80px;
                margin-right: auto;
                margin-left: auto;
            }
            .section-two .section-item-title{
                color: var(--clr-blue-dark);
                font-size: 1.8rem;
                font-weight: 600;
            }
            .section-two .text{
                margin: 0.9rem 0;
            }

            /* footer */
            .footer{
                padding: 3rem 0;
            }
            .footer-content p{
                color: var(--clr-grey);
            }
            .footer-content p span{
                color: var(--clr-white);
            }

            /* media queries */
            @media screen and (min-width: 768px){
                .section-two .section-items{
                    grid-template-columns: repeat(2, 1fr);
                }
            }

            @media screen and (min-width: 992px){
                .section-one-content{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    column-gap: 3rem;
                }
                .section-one-r{
                    text-align: left;
                }
                .section-two .section-items{
                    grid-template-columns: repeat(3, 1fr);
                }
                .section-two .section-item{
                    text-align: left;
                }
                .section-two .section-item-icon img{
                    margin-left: 0;
                }
            }



            /* resume page */
            #about-sc{
                padding: 64px 0;
            }

            .cv-form-row-title{
                background-color: var(--clr-dark);
                padding: 0.8rem 1.6rem;
                margin-bottom: 2rem;
            }

            .cv-form-row-title h3{
                color: var(--clr-white);
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                font-size: 1.7rem;
            }
            .cv-form-blk{
                margin: 3rem 0;
            }
            .cv-form-row{
                padding: 3rem 2rem 0 2rem;
                border: 1px solid rgba(0, 0, 0, 0.08);
                margin-bottom: 1rem;
                position: relative;
            }
            textarea{
                resize: none;
            }
            .form-elem{
                margin-bottom: 3rem;
                position: relative;
            }
            .form-label{
                display: block;
                font-weight: 600;
                font-size: 14px;
                color: var(--clr-dark);
                margin-bottom: 0.5rem;
            }
            .form-control{
                border-radius: none;
                border: 1px solid rgba(0, 0, 0, 0.1);
                font-size: 14px;
                padding: 0.8rem 1.6rem;
                font-family: inherit;
                width: 100%;
                outline: 0;
                transition: var(--transition);
            }

            .form-control:focus{
                border-color: rgba(0, 0, 0, 0.3);
            }
            .form-text{
                color: #ca0b00;
                font-size: 12px;
                position: absolute;
                letter-spacing: 0.5px;
                top: calc(100% + 2px);
                left: 0;
                width: 100%;
            }
            .cols-3, .cols-2{
                display: grid;
            }
            .repeater-add-btn{
                width: 25px;
                height: 25px;
                background-color: var(--clr-blue-mid);
                font-size: 1.6rem;
                color: var(--clr-white);
                margin: 1rem 0;
            }
            .repeater-remove-btn{
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 999;
                width: 25px;
                height: 25px;
                border-radius: 50%;
                background-color: #ca0b00;
                color: var(--clr-white);
                font-size: 1.6rem;
            }

            /* preview section */
            .preview-cnt{
                border-radius: 5px;
                display: grid;
                grid-template-columns: 32% auto;
                box-shadow: rgba(149, 157, 165, 0.2) 0px 8px 24px;
                overflow: hidden;
            }

            .preview-cnt-l{
                padding: 3rem 3rem 2rem 3rem;
            }
            .preview-cnt-r{
                padding: 3rem 3rem 3rem 4rem;
            }
            .preview-cnt-l .preview-blk:nth-child(1){
                text-align: center;
            }
            .preview-image{
                width: 120px;
                height: 120px;
                border-radius: 50%;
                overflow: hidden;
                margin-right: auto;
                margin-left: auto;
            }
            .preview-image img{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            .preview-item-name{
                font-size: 2.4rem;
                font-weight: 600;
                margin: 1.8rem 0;
                position: relative;
            }
            .preview-item-name::after{
                position: absolute;
                content: "";
                bottom: -10px;
                width: 50px;
                height: 1.5px;
                background-color: rgba(255, 255, 255, 0.5);
                left: 50%;
                transform: translateX(-50%);
            }
            .preview-blk{
                padding: 1rem 0;
                margin-bottom: 1rem;
            }
            .preview-blk-title h3{
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 0.5px solid rgba(0, 0, 0, 0.08);
                padding-bottom: 0.5rem;
            }
            .preview-blk-title{
                margin-bottom: 1rem;
            }
            .preview-blk-list .preview-item{
                font-size: 1.5rem;
                margin-bottom: 0.2rem;
                opacity: 0.95;
            }
            .preview-cnt-r .preview-blk-title{
                color: var(--clr-dark);
            }
            .preview-cnt-r .preview-blk-list .preview-item{
                margin-top: 1.8rem;
            }

            .achievements-items.preview-blk-list .preview-item span:first-child,
            .educations-items.preview-blk-list .preview-item span:first-child,
            .experiences-items.preview-blk-list .preview-item span:first-child{
                display: block;
                font-weight: 600;
                margin-bottom: 1rem;
                background-color: rgba(0, 0, 0, 0.03);
            }

            .educations-items.preview-blk-list .preview-item span:nth-child(2),
            .experiences-items.preview-blk-list .preview-item span:nth-child(2){
                font-weight: 600;
                margin-right: 1rem;
            }

            .educations-items.preview-blk-list .preview-item span:nth-child(3),
            .experiences-items.preview-blk-list .preview-item span:nth-child(3){
                font-style: italic;
                margin-right: 1rem;
            }

            .educations-items.preview-blk-list .preview-item span:nth-child(4),
            .educations-items.preview-blk-list .preview-item span:nth-child(5),
            .experiences-items.preview-blk-list .preview-item span:nth-child(4),
            .experiences-items.preview-blk-list .preview-item span:nth-child(5){
                margin-right: 1rem;
                background-color: var(--clr-green);
                color: var(--clr-white);
                padding: 0 1rem;
                border-radius: 0.6rem;
            }

            .educations-items.preview-blk-list .preview-item span:nth-child(6),
            .experiences-items.preview-blk-list .preview-item span:nth-child(6){
                font-size: 13.5px;
                display: block;
                opacity: 0.8;
                margin-top: 1rem;
            }
            .projects-items.preview-blk-list .preview-item span{
                display: block;
            }

            @media screen and (min-width: 768px){
                .cols-3{
                    grid-template-columns: repeat(3, 1fr);
                    column-gap: 2rem;
                }
                .cols-2{
                    grid-template-columns: repeat(2, 1fr);
                    column-gap: 2rem;
                }
            }

            @media screen and (min-width: 992px){
                .cv-form-row{
                    padding: 3rem 3rem 0rem 3rem;
                }
                .cols-3{
                    grid-template-columns: repeat(3, 1fr);
                }
            }

            .print-btn-sc{
                margin: 2rem 0 6rem 0;
            }

            /* print section */
            @media print{
                body *{
                    visibility: hidden;
                }

                .non_print_area{
                    display: none;
                }

                .print_area, .print_area *{
                    visibility: visible;
                }

                .print_area{
                    width: 100%;
                    position: absolute;
                    left: 0;
                    top: 0;
                    overflow: hidden;
                }
            }
            </style>
            <body>
                <nav class = "navbar bg-white">
                    <div class="container">
                        <div class = "navbar-content">
                            <div class = "brand-and-toggler">
                                <a href = "index.html" class = "navbar-brand">
                                    <img src = "assets/images/curriculum-vitae.png" alt = "" class = "navbar-brand-icon">
                                    <span class = "navbar-brand-text">build <span>resume.</span>
                                </a>
                                <button type = "button" class = "navbar-toggler-btn">
                                    <div class = "bars">
                                        <div class = "bar"></div>
                                        <div class = "bar"></div>
                                        <div class = "bar"></div>
                                    </div>
                                </button>
                            </div>
                        </div>
                    </div>
                </nav>

                <section id = "about-sc" class = "">
                    <div class = "container">
                        <div class = "about-cnt">
                            <form action="" class="cv-form" id = "cv-form">
                                <div class = "cv-form-blk">
                                    <div class = "cv-form-row-title">
                                        <h3>about section</h3>
                                    </div>
                                    <div class = "cv-form-row cv-form-row-about">
                                        <div class = "cols-3">
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">First Name</label>
                                                <input name = "firstname" type = "text" class = "form-control firstname" id = "" onkeyup="generateCV()" placeholder="e.g. John">
                                                <span class="form-text"></span>
                                            </div>
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Middle Name <span class = "opt-text">(optional)</span></label>
                                                <input name = "middlename" type = "text" class = "form-control middlename" id = "" onkeyup="generateCV()" placeholder="e.g. Herbert">
                                                <span class="form-text"></span>
                                            </div>
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Last Name</label>
                                                <input name = "lastname" type = "text" class = "form-control lastname" id = "" onkeyup="generateCV()" placeholder="e.g. Doe">
                                                <span class="form-text"></span>
                                            </div>
                                        </div>

                                        <div class="cols-3">
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Your Image</label>
                                                <input name = "image" type = "file" class = "form-control image" id = "" accept = "image/*" onchange="previewImage()">
                                            </div>
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Designation</label>
                                                <input name = "designation" type = "text" class = "form-control designation" id = "" onkeyup="generateCV()" placeholder="e.g. Sr.Accountants">
                                                <span class="form-text"></span>
                                            </div>
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Address</label>
                                                <input name = "address" type = "text" class = "form-control address" id = "" onkeyup="generateCV()" placeholder="e.g. Lake Street-23">
                                                <span class="form-text"></span>
                                            </div>
                                        </div>

                                        <div class = "cols-3">
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Email</label>
                                                <input name = "email" type = "text" class = "form-control email" id = "" onkeyup="generateCV()" placeholder="e.g. johndoe@gmail.com">
                                                <span class="form-text"></span>
                                            </div>
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Phone No:</label>
                                                <input name = "phoneno" type = "text" class = "form-control phoneno" id = "" onkeyup="generateCV()" placeholder="e.g. 456-768-798, 567.654.002">
                                                <span class="form-text"></span>
                                            </div>
                                            <div class = "form-elem">
                                                <label for = "" class = "form-label">Summary</label>
                                                <input name = "summary" type = "text" class = "form-control summary" id = "" onkeyup="generateCV()" placeholder="e.g. Doe">
                                                <span class="form-text"></span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="cv-form-blk">
                                    <div class = "cv-form-row-title">
                                        <h3>achievements</h3>
                                    </div>

                                    <div class = "row-separator repeater">
                                        <div class = "repeater" data-repeater-list = "group-a">
                                            <div data-repeater-item>
                                                <div class = "cv-form-row cv-form-row-achievement">
                                                    <div class = "cols-2">
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Title</label>
                                                            <input name = "achieve_title" type = "text" class = "form-control achieve_title" id = "" onkeyup="generateCV()" placeholder="e.g. johndoe@gmail.com">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Description</label>
                                                            <input name = "achieve_description" type = "text" class = "form-control achieve_description" id = "" onkeyup="generateCV()" placeholder="e.g. johndoe@gmail.com">
                                                            <span class="form-text"></span>
                                                        </div>
                                                    </div>
                                                    <button data-repeater-delete type = "button" class = "repeater-remove-btn">-</button>
                                                </div>
                                            </div>
                                        </div>
                                        <button type = "button" data-repeater-create value = "Add" class = "repeater-add-btn">+</button>
                                    </div>
                                </div>

                                <div class="cv-form-blk">
                                    <div class = "cv-form-row-title">
                                        <h3>experience</h3>
                                    </div>

                                    <div class = "row-separator repeater">
                                        <div class = "repeater" data-repeater-list = "group-b">
                                            <div data-repeater-item>
                                                <div class = "cv-form-row cv-form-row-experience">
                                                    <div class = "cols-3">
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Title</label>
                                                            <input name = "exp_title" type = "text" class = "form-control exp_title" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Company / Organization</label>
                                                            <input name = "exp_organization" type = "text" class = "form-control exp_organization" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Location</label>
                                                            <input name = "exp_location" type = "text" class = "form-control exp_location" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                    </div>

                                                    <div class = "cols-3">
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Start Date</label>
                                                            <input name = "exp_start_date" type = "date" class = "form-control exp_start_date" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">End Date</label>
                                                            <input name = "exp_end_date" type = "date" class = "form-control exp_end_date" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Description</label>
                                                            <input name = "exp_description" type = "text" class = "form-control exp_description" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                    </div>

                                                    <button data-repeater-delete type = "button" class = "repeater-remove-btn">-</button>
                                                </div>
                                            </div>
                                        </div>
                                        <button type = "button" data-repeater-create value = "Add" class = "repeater-add-btn">+</button>
                                    </div>
                                </div>

                                <div class="cv-form-blk">
                                    <div class = "cv-form-row-title">
                                        <h3>education</h3>
                                    </div>

                                    <div class = "row-separator repeater">
                                        <div class = "repeater" data-repeater-list = "group-c">
                                            <div data-repeater-item>
                                                <div class = "cv-form-row cv-form-row-experience">
                                                    <div class = "cols-3">
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">School</label>
                                                            <input name = "edu_school" type = "text" class = "form-control edu_school" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Degree</label>
                                                            <input name = "edu_degree" type = "text" class = "form-control edu_degree" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">City</label>
                                                            <input name = "edu_city" type = "text" class = "form-control edu_city" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                    </div>

                                                    <div class = "cols-3">
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Start Date</label>
                                                            <input name = "edu_start_date" type = "date" class = "form-control edu_start_date" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">End Date</label>
                                                            <input name = "edu_graduation_date" type = "date" class = "form-control edu_graduation_date" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Description</label>
                                                            <input name = "edu_description" type = "text" class = "form-control edu_description" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                    </div>

                                                    <button data-repeater-delete type = "button" class = "repeater-remove-btn">-</button>
                                                </div>
                                            </div>
                                        </div>
                                        <button type = "button" data-repeater-create value = "Add" class = "repeater-add-btn">+</button>
                                    </div>
                                </div>

                                <div class="cv-form-blk">
                                    <div class = "cv-form-row-title">
                                        <h3>projects</h3>
                                    </div>

                                    <div class = "row-separator repeater">
                                        <div class = "repeater" data-repeater-list = "group-d">
                                            <div data-repeater-item>
                                                <div class = "cv-form-row cv-form-row-experience">
                                                    <div class = "cols-3">
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Project Name</label>
                                                            <input name = "proj_title" type = "text" class = "form-control proj_title" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Project link</label>
                                                            <input name = "proj_link" type = "text" class = "form-control proj_link" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                        <div class = "form-elem">
                                                            <label for = "" class = "form-label">Description</label>
                                                            <input name = "proj_description" type = "text" class = "form-control proj_description" id = "" onkeyup="generateCV()">
                                                            <span class="form-text"></span>
                                                        </div>
                                                    </div>
                                                    <button data-repeater-delete type = "button" class = "repeater-remove-btn">-</button>
                                                </div>
                                            </div>
                                        </div>
                                        <button type = "button" data-repeater-create value = "Add" class = "repeater-add-btn">+</button>
                                    </div>
                                </div>

                                <div class="cv-form-blk">
                                    <div class = "cv-form-row-title">
                                        <h3>skills</h3>
                                    </div>

                                    <div class = "row-separator repeater">
                                        <div class = "repeater" data-repeater-list = "group-e">
                                            <div data-repeater-item>
                                                <div class = "cv-form-row cv-form-row-skills">
                                                    <div class = "form-elem">
                                                        <label for = "" class = "form-label">Skill</label>
                                                        <input name = "skill" type = "text" class = "form-control skill" id = "" onkeyup="generateCV()">
                                                        <span class="form-text"></span>
                                                    </div>
                                                    
                                                    <button data-repeater-delete type = "button" class = "repeater-remove-btn">-</button>
                                                </div>
                                            </div>
                                        </div>
                                        <button type = "button" data-repeater-create value = "Add" class = "repeater-add-btn">+</button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </section>

                <section id = "preview-sc" class = "print_area">
                    <div class = "container">
                        <div class = "preview-cnt">
                            <div class = "preview-cnt-l bg-green text-white">
                                <div class = "preview-blk">
                                    <div class = "preview-image">
                                        <img src = "" alt = "" id = "image_dsp"> 
                                    </div>
                                    <div class = "preview-item preview-item-name">
                                        <span class = "preview-item-val fw-6" id = "fullname_dsp"></span>
                                    </div>
                                    <div class = "preview-item">
                                        <span class = "preview-item-val text-uppercase fw-6 ls-1" id = "designation_dsp"></span>
                                    </div>
                                </div>

                                <div class = "preview-blk">
                                    <div class = "preview-blk-title">
                                        <h3>about</h3>
                                    </div>
                                    <div class = "preview-blk-list">
                                        <div class = "preview-item">
                                            <span class = "preview-item-val" id = "phoneno_dsp"></span>
                                        </div>
                                        <div class = "preview-item">
                                            <span class = "preview-item-val" id = "email_dsp"></span>
                                        </div>
                                        <div class = "preview-item">
                                            <span class = "preview-item-val" id = "address_dsp"></span>
                                        </div>
                                        <div class = "preview-item">
                                            <span class = "preview-item-val" id = "summary_dsp"></span>
                                        </div>
                                    </div>
                                </div>

                                <div class = "preview-blk">
                                    <div class = "preview-blk-title">
                                        <h3>skills</h3>
                                    </div>
                                    <div class = "skills-items preview-blk-list" id = "skills_dsp">
                                        <!-- skills list here -->
                                    </div>
                                </div>
                            </div>

                            <div class = "preview-cnt-r bg-white">
                                <div class = "preview-blk">
                                    <div class = "preview-blk-title">
                                        <h3>Achievements</h3>
                                    </div>
                                    <div class = "achievements-items preview-blk-list" id = "achievements_dsp"></div>
                                </div>

                                <div class = "preview-blk">
                                    <div class = "preview-blk-title">
                                        <h3>educations</h3>
                                    </div>
                                    <div class = "educations-items preview-blk-list" id = "educations_dsp"></div>
                                </div>

                                <div class = "preview-blk">
                                    <div class = "preview-blk-title">
                                        <h3>experiences</h3>
                                    </div>
                                    <div class = "experiences-items preview-blk-list" id = "experiences_dsp"></div>
                                </div>

                                <div class = "preview-blk">
                                    <div class = "preview-blk-title">
                                        <h3>projects</h3>
                                    </div>
                                    <div class = "projects-items preview-blk-list" id = "projects_dsp"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section class = "print-btn-sc">
                    <div class = "container">
                        <button type = "button" class = "print-btn btn btn-primary" onclick="printCV()">Print CV</button>
                    </div>
                </section>


                

                <!-- jquery cdn -->
                <script src="https://code.jquery.com/jquery-3.6.4.js" integrity="sha256-a9jBBRygX1Bh5lt8GZjXDzyOB+bWve9EiO7tROUtj/E=" crossorigin="anonymous"></script>
                <!-- jquery repeater cdn -->
                <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.repeater/1.2.1/jquery.repeater.js" integrity="sha512-bZAXvpVfp1+9AUHQzekEZaXclsgSlAeEnMJ6LfFAvjqYUVZfcuVXeQoN5LhD7Uw0Jy4NCY9q3kbdEXbwhZUmUQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
                <!-- custom js -->
                <script src = "assets/js/script.js"></script>
                <!-- app js -->
                <script src="assets/js/app.js"></script>
                <script>
                // regex for validation
                const strRegex =  /^[a-zA-Z\s]*$/; // containing only letters
                const emailRegex = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
                const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/im;
                /* supports following number formats - (123) 456-7890, (123)456-7890, 123-456-7890, 123.456.7890, 1234567890, +31636363634, 075-63546725 */
                const digitRegex = /^\d+$/;

                const mainForm = document.getElementById('cv-form');
                const validType = {
                    TEXT: 'text',
                    TEXT_EMP: 'text_emp',
                    EMAIL: 'email',
                    DIGIT: 'digit',
                    PHONENO: 'phoneno',
                    ANY: 'any',
                }

                // user inputs elements
                let firstnameElem = mainForm.firstname,
                    middlenameElem = mainForm.middlename,
                    lastnameElem = mainForm.lastname,
                    imageElem = mainForm.image,
                    designationElem = mainForm.designation,
                    addressElem = mainForm.address,
                    emailElem = mainForm.email,
                    phonenoElem = mainForm.phoneno,
                    summaryElem = mainForm.summary;

                // display elements
                let nameDsp = document.getElementById('fullname_dsp'),
                    imageDsp = document.getElementById('image_dsp'),
                    phonenoDsp = document.getElementById('phoneno_dsp'),
                    emailDsp = document.getElementById('email_dsp'),
                    addressDsp = document.getElementById('address_dsp'),
                    designationDsp = document.getElementById('designation_dsp'),
                    summaryDsp = document.getElementById('summary_dsp'),
                    projectsDsp = document.getElementById('projects_dsp'),
                    achievementsDsp = document.getElementById('achievements_dsp'),
                    skillsDsp = document.getElementById('skills_dsp'),
                    educationsDsp = document.getElementById('educations_dsp'),
                    experiencesDsp = document.getElementById('experiences_dsp');

                // first value is for the attributes and second one passes the nodelists
                const fetchValues = (attrs, ...nodeLists) => {
                    let elemsAttrsCount = nodeLists.length;
                    let elemsDataCount = nodeLists[0].length;
                    let tempDataArr = [];

                    // first loop deals with the no of repeaters value
                    for(let i = 0; i < elemsDataCount; i++){
                        let dataObj = {}; // creating an empty object to fill the data
                        // second loop fetches the data for each repeaters value or attributes 
                        for(let j = 0; j < elemsAttrsCount; j++){
                            // setting the key name for the object and fill it with data
                            dataObj[`${attrs[j]}`] = nodeLists[j][i].value;
                        }
                        tempDataArr.push(dataObj);
                    }

                    return tempDataArr;
                }

                const getUserInputs = () => {

                    // achivements 
                    let achievementsTitleElem = document.querySelectorAll('.achieve_title'),
                    achievementsDescriptionElem = document.querySelectorAll('.achieve_description');

                    // experiences
                    let expTitleElem = document.querySelectorAll('.exp_title'),
                    expOrganizationElem = document.querySelectorAll('.exp_organization'),
                    expLocationElem = document.querySelectorAll('.exp_location'),
                    expStartDateElem = document.querySelectorAll('.exp_start_date'),
                    expEndDateElem = document.querySelectorAll('.exp_end_date'),
                    expDescriptionElem = document.querySelectorAll('.exp_description');

                    // education
                    let eduSchoolElem = document.querySelectorAll('.edu_school'),
                    eduDegreeElem = document.querySelectorAll('.edu_degree'),
                    eduCityElem = document.querySelectorAll('.edu_city'),
                    eduStartDateElem = document.querySelectorAll('.edu_start_date'),
                    eduGraduationDateElem = document.querySelectorAll('.edu_graduation_date'),
                    eduDescriptionElem = document.querySelectorAll('.edu_description');

                    let projTitleElem = document.querySelectorAll('.proj_title'),
                    projLinkElem = document.querySelectorAll('.proj_link'),
                    projDescriptionElem = document.querySelectorAll('.proj_description');

                    let skillElem = document.querySelectorAll('.skill');

                    // event listeners for form validation
                    firstnameElem.addEventListener('keyup', (e) => validateFormData(e.target, validType.TEXT, 'First Name'));
                    middlenameElem.addEventListener('keyup', (e) => validateFormData(e.target, validType.TEXT_EMP, 'Middle Name'));
                    lastnameElem.addEventListener('keyup', (e) => validateFormData(e.target, validType.TEXT, 'Last Name'));
                    phonenoElem.addEventListener('keyup', (e) => validateFormData(e.target, validType.PHONENO, 'Phone Number'));
                    emailElem.addEventListener('keyup', (e) => validateFormData(e.target, validType.EMAIL, 'Email'));
                    addressElem.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Address'));
                    designationElem.addEventListener('keyup', (e) => validateFormData(e.target, validType.TEXT, 'Designation'));

                    achievementsTitleElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Title')));
                    achievementsDescriptionElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Description')));
                    expTitleElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Title')));
                    expOrganizationElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Organization')));
                    expLocationElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, "Location")));
                    expStartDateElem.forEach(item => item.addEventListener('blur', (e) => validateFormData(e.target, validType.ANY, 'End Date')));
                    expEndDateElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'End Date')));
                    expDescriptionElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Description')));
                    eduSchoolElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'School')));
                    eduDegreeElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Degree')));
                    eduCityElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'City')));
                    eduStartDateElem.forEach(item => item.addEventListener('blur', (e) => validateFormData(e.target, validType.ANY, 'Start Date')));
                    eduGraduationDateElem.forEach(item => item.addEventListener('blur', (e) => validateFormData(e.target, validType.ANY, 'Graduation Date')));
                    eduDescriptionElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Description')));
                    projTitleElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Title')));
                    projLinkElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Link')));
                    projDescriptionElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'Description')));
                    skillElem.forEach(item => item.addEventListener('keyup', (e) => validateFormData(e.target, validType.ANY, 'skill')));

                    return {
                        firstname: firstnameElem.value,
                        middlename: middlenameElem.value,
                        lastname: lastnameElem.value,
                        designation: designationElem.value,
                        address: addressElem.value,
                        email: emailElem.value,
                        phoneno: phonenoElem.value,
                        summary: summaryElem.value,
                        achievements: fetchValues(['achieve_title', 'achieve_description'], achievementsTitleElem, achievementsDescriptionElem),
                        experiences: fetchValues(['exp_title', 'exp_organization', 'exp_location', 'exp_start_date', 'exp_end_date', 'exp_description'], expTitleElem, expOrganizationElem, expLocationElem, expStartDateElem, expEndDateElem, expDescriptionElem),
                        educations: fetchValues(['edu_school', 'edu_degree', 'edu_city', 'edu_start_date', 'edu_graduation_date', 'edu_description'], eduSchoolElem, eduDegreeElem, eduCityElem, eduStartDateElem, eduGraduationDateElem, eduDescriptionElem),
                        projects: fetchValues(['proj_title', 'proj_link', 'proj_description'], projTitleElem, projLinkElem, projDescriptionElem),
                        skills: fetchValues(['skill'], skillElem)
                    }
                };

                function validateFormData(elem, elemType, elemName){
                    // checking for text string and non empty string
                    if(elemType == validType.TEXT){
                        if(!strRegex.test(elem.value) || elem.value.trim().length == 0) addErrMsg(elem, elemName);
                        else removeErrMsg(elem);
                    }

                    // checking for only text string
                    if(elemType == validType.TEXT_EMP){
                        if(!strRegex.test(elem.value)) addErrMsg(elem, elemName);
                        else removeErrMsg(elem);
                    }

                    // checking for email
                    if(elemType == validType.EMAIL){
                        if(!emailRegex.test(elem.value) || elem.value.trim().length == 0) addErrMsg(elem, elemName);
                        else removeErrMsg(elem);
                    }

                    // checking for phone number
                    if(elemType == validType.PHONENO){
                        if(!phoneRegex.test(elem.value) || elem.value.trim().length == 0) addErrMsg(elem, elemName);
                        else removeErrMsg(elem);
                    }

                    // checking for only empty
                    if(elemType == validType.ANY){
                        if(elem.value.trim().length == 0) addErrMsg(elem, elemName);
                        else removeErrMsg(elem);
                    }
                }

                // adding the invalid text
                function addErrMsg(formElem, formElemName){
                    formElem.nextElementSibling.innerHTML = `${formElemName} is invalid`;
                }

                // removing the invalid text 
                function removeErrMsg(formElem){
                    formElem.nextElementSibling.innerHTML = "";
                }

                // show the list data
                const showListData = (listData, listContainer) => {
                    listContainer.innerHTML = "";
                    listData.forEach(listItem => {
                        let itemElem = document.createElement('div');
                        itemElem.classList.add('preview-item');
                        
                        for(const key in listItem){
                            let subItemElem = document.createElement('span');
                            subItemElem.classList.add('preview-item-val');
                            subItemElem.innerHTML = `${listItem[key]}`;
                            itemElem.appendChild(subItemElem);
                        }

                        listContainer.appendChild(itemElem);
                    })
                }

                const displayCV = (userData) => {
                    nameDsp.innerHTML = userData.firstname + " " + userData.middlename + " " + userData.lastname;
                    phonenoDsp.innerHTML = userData.phoneno;
                    emailDsp.innerHTML = userData.email;
                    addressDsp.innerHTML = userData.address;
                    designationDsp.innerHTML = userData.designation;
                    summaryDsp.innerHTML = userData.summary;
                    showListData(userData.projects, projectsDsp);
                    showListData(userData.achievements, achievementsDsp);
                    showListData(userData.skills, skillsDsp);
                    showListData(userData.educations, educationsDsp);
                    showListData(userData.experiences, experiencesDsp);
                }

                // generate CV
                const generateCV = () => {
                    let userData = getUserInputs();
                    displayCV(userData);
                    console.log(userData);
                }

                function previewImage(){
                    let oFReader = new FileReader();
                    oFReader.readAsDataURL(imageElem.files[0]);
                    oFReader.onload = function(ofEvent){
                        imageDsp.src = ofEvent.target.result;
                    }
                }

                // print CV
                function printCV(){
                    window.print();
                }
                </script>
                <script>
                // form repeater
                $(document).ready(function(){
                    $('.repeater').repeater({
                        initEmpty: false,
                        defaultValues: {
                            'text-input': ''
                        },
                        show:function(){
                            $(this).slideDown();
                        },
                        hide: function(deleteElement){
                            $(this).slideUp(deleteElement);
                            setTimeout(() => {
                                generateCV();
                            }, 500);
                        },
                        isFirstItemUndeletable: true
                    })
                })
                </script>
            </body>
        </html>
        """
        # writing the code into the file
        f.write(html_template)

        # close the file
        f.close()

        # 1st method how to open html files in chrome using
        filename = 'file:///'+os.getcwd()+'/' + 'GFG.html'
        webbrowser.open_new_tab(filename)

        
        
    else:
        # Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'abcd' and ad_password == '0123':
                st.success("Welcome Sourav")
                # Display Data
                cursor.execute('''SELECT*FROM user_details''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(
                    df, 'User_Details.csv', 'Download Report'), unsafe_allow_html=True)
                # Admin Side Data
                query = 'select * from user_details;'
                plot_data = pd.read_sql(query, connection)

                # Pie chart for predicted field recommendations
                labels = plot_data.Predicted_Field.unique()
                print(labels)
                values = plot_data.Predicted_Field.value_counts()
                print(values)
                st.subheader(
                    "📈 **Pie-Chart for Predicted Field Recommendations**")
                fig = px.pie(df, values=values, names=labels,
                             title='Predicted Field according to the Skills')
                st.plotly_chart(fig)

                # Pie chart for User's👨‍💻 Experienced Level
                labels = plot_data.User_level.unique()
                values = plot_data.User_level.value_counts()
                st.subheader(
                    "📈 ** Pie-Chart for User's👨‍💻 Experienced Level**")
                fig = px.pie(df, values=values, names=labels,
                             title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                st.plotly_chart(fig)

            else:
                st.error("Wrong ID & Password Provided")


run()
