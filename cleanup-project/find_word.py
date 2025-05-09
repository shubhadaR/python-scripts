def tail_log_file(file_path, keyword):
    with open(file_path, "r") as file:
        with open("error.log", "a") as file_write:
        #line_end=file.seek(0,2)
            for line in file.readlines():
                if keyword in line:
                    file_write.write(f"Found error:{line}")
    print(file_write.closed)

def main():
    tail_log_file("script.log", "ERROR" )
 
if __name__== "__main__":
    main()

