import os
import logging

logging.basicConfig(filename='script.log', level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

logging.info("script started")
def create_file (dir, name, count, ext):
    for i in range(1, count+1):
        filename= f"{name}{i}.{ext}"
        file_path= os.path.join(dir, filename)
        if not os.path.exists(file_path):
            with open (file_path, "w") as file:
                pass
            logging.info(f"created {file_path} successfully")
        else:
            logging.error(f" file {file_path} already exist")


def cleanup_tmp(dir):
    list_file= os.listdir(dir)
    count=0
    for i in list_file:
        file=os.path.join(dir, i)
        if file.endswith(".tmp"):
                count=count+1
                os.remove(file)
                logging.info(f"file {file} deleted successfully")
    logging.error(f"No tmp file found") if count ==0 else logging.info(f"{count} files deleted")


def main():

    dir= "logs"
    name= input("enter name of file")
    count= int(input("enter count of file"))
    ext= input("enter ext of file")

    create_file(dir, name, count, ext)
    cleanup_tmp(dir)

    logging.info(f"After cleanup log dir: {os.listdir(dir)}")

if __name__=="__main__":
    main()
