#Script - extractor de plan de actividades a Markdown

#get user data login from file
#the file coulb be contain only the user and password with and line break:
#   user
#   password
with open("data.user", "r") as f:
    data_user = f.readline()
    data_pass = f.readline()

#import libraries
import re
from os import remove
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

try:
    
    #set driver path
    service = webdriver.FirefoxService("geckodriver")

    #start firefox bot with driver
    d = webdriver.Firefox(service = service)
    d.get("https://uam.terna.net/") #get page

    #give user
    user = d.find_element(By.NAME, "username")
    user.send_keys(data_user)

    #give password
    password = d.find_element(By.NAME, "password")
    password.send_keys(data_pass)

    #button login
    btn_login = d.find_element(By.XPATH, "/html/body/header/nav/div/div[2]/form/button")
    btn_login.click()

    # ------------------------------ loggin succesx ------------------------------ #
    d.get("https://uam.terna.net/VerNotasLapso.php?mid=0")

    #download the page
    with open("index.html", "w") as f:
        f.write(d.page_source)
        
    d.quit()
    
    # ----------------------------- download success ----------------------------- #
    filehtml = open("index.html", "r") #open html data
    content = filehtml.read()
    filehtml.close()

    p = BeautifulSoup(content, "html.parser") #init library

    #subject names
    subjects = {}
    td = p.find_all("td", {"class":"table-sub-title"})

    #create template
    for x in td:
        x = re.sub(r".*?\s\dM[ABC]?\s", "", x.text.replace("\n", "")) #remove id code
        x = re.sub(r"\s+", " ", x).strip()
        
        subjects[x] = {"c1" : None, "c2" : None, "c3" : None} #define key with the subject name and a sub dict with lapses to fill
        
    keys_names = list(subjects.keys()) #save the subjects names
        
    #subjects content
    td = p.find_all("td", {"class":"text-left"})

    #in this point the loop searchs the subject content and make a format {date-content}
    i = 0
    for K in range(len(keys_names)):
        loop = True
        string = []
        temp_str = []
        
        while loop == True:
            t = td[i].text.strip()
            
            if len(t) > 26:
                date = re.search(r"\d{2}-\d{2}-\d{4}", t).group()
                
                #split the string in name activity and content
                t = re.split(r"\s?\d{2}-\d{2}-\d{4}", t)
                
                t_activity = re.sub(r"(\d.?\s?)+\s", "", t[0])
                t_content = re.sub(r"\s+", " ", t[1]).replace(" ,", ",").replace(",", ", ")
                
                if t_content == "":
                    temp_str.append(t_activity + "/" + date + "/" + "None" + "\n")
                else:
                    temp_str.append(t_activity + "/" + date + "/" + t_content + "\n")
            
            else:
                if re.search("C1. 1er Corte", t) or re.search("C2. 2do Corte", t):
                    string.append(temp_str)
                    temp_str = []
                
                elif re.search("C3. 3er Corte", t):
                    string.append(temp_str)
                    loop = False
                
            i += 1
        
        subjects[keys_names[K]]["c1"] = string[0]
        subjects[keys_names[K]]["c2"] = string[1]
        subjects[keys_names[K]]["c3"] = string[2]
    
    #DONE UNTILL THIS PART, THE SUBJECTS AND ACTIVITIES WAS EXTRACTED AT THIS POINT
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    lapses_names = {"c1": "1er Corte", "c2": "2do Corte", "c3": "3er Corte"}

    # create the markdown file
    md_file = open("output.md", "w")

    for sub_name, corte in subjects.items():
        md_file.write(f'## <b style="color:pink">{sub_name}</b>\n')
        for corte, tema in corte.items():
            md_file.write(f"### **{lapses_names[corte]}**\n")
            for value in tema:
                #extract the values from the string
                fecha = re.search(r"\d{2}-\d{2}-\d{4}", value).group() 
                dia_semana = datetime.strptime(fecha, "%d-%m-%Y").weekday()
                tipo_actividad = re.split(r"/", value)[0]
                contenido = re.sub(r".*\d{2}-\d{2}-\d{4}\/", "", value).replace("\n", "")
                
                title = f"- [ ] {tipo_actividad} ({day_names[dia_semana]} {re.sub(r"-", " - ", fecha)})\n"
                
                if contenido != "None":
                    value = f'    <p style="color: #888">[{contenido}]</p>\n'
                else:
                    value = ""
                    
                md_file.write(title)
                if value != "":
                    md_file.write(value)
                    
            md_file.write("</br>\n")

    md_file.close()
    remove("index.html")

except Exception as e:
    print(e)
    d.quit()
