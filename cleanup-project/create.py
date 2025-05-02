import os

log_dir= "logs"

for number in range (1, 4):
    filename= f"log{number}.txt"
    file_path= os.path.join(log_dir,filename)
    with open (file_path, "w") as file:
        pass
    print(f"created {file_path} successfully")
