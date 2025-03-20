__path = '../../styles/'

def load_stylesheet(file_name, elem):
    with open(__path + file_name, "r") as file:
        elem.setStyleSheet(file.read())