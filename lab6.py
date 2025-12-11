import xml.etree.ElementTree as ET
import os
from datetime import datetime
import sys

class FileNotFoundError(Exception): pass
class FileCorruptedError(Exception): pass

class XMLFileHandler:
    
    PRIORITY_ORDER = {"High": 1, "Medium": 2, "Low": 3}

    @staticmethod
    def _prettify(elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip(): elem.text = i + "  "
            if not elem.tail or not elem.tail.strip(): elem.tail = i
            for elem_child in elem:
                XMLFileHandler._prettify(elem_child, level + 1)
            if not elem.tail or not elem.tail.strip(): elem.tail = i
        elif level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

    def logged(mode):
        def decorator(func):
            def wrapper(*args, **kwargs):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_message = f"[{timestamp}] Method called: {func.__name__}"
                if mode == "console":
                    print(log_message, file=sys.stderr) 
                if mode == "file":
                    with open("file_operations.log", "a", encoding="utf-8") as f:
                        f.write(log_message + "\n")
                
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = f"[{timestamp}] Error in {func.__name__}: {str(e)}"
                    if mode == "console":
                        print(error_msg, file=sys.stderr)
                    if mode == "file":
                        with open("file_operations.log", "a", encoding="utf-8") as f:
                            f.write(error_msg + "\n")
                    raise
            return wrapper
        return decorator

    def __init__(self, filename):
        if not filename: raise ValueError("Filename cannot be empty!")
        if not filename.endswith('.xml'): filename += '.xml'
        self.__filename = filename
    
    @property
    def filename(self): return self.__filename
    
    def _check_file_exists(self):
        if not os.path.exists(self.__filename):
            raise FileNotFoundError(f"File '{self.__filename}' not found!")
    
    @logged(mode="console")
    def create(self, root_name="data"):
        try:
            root = ET.Element(root_name)
            self._prettify(root) 
            ET.ElementTree(root).write(self.__filename, encoding="utf-8", xml_declaration=True)
            print(f"File '{self.__filename}' successfully created!")
            return True
        except Exception as e:
            raise FileCorruptedError(f"Error creating file: {str(e)}")
    
    @logged(mode="console")
    def read(self):
        self._check_file_exists()
        try:
            return ET.parse(self.__filename).getroot()
        except ET.ParseError:
            raise FileCorruptedError(f"File '{self.__filename}' is corrupted!")
        except PermissionError:
            raise FileCorruptedError(f"Access denied to file '{self.__filename}'!")
    
    @logged(mode="file")
    def write(self, root_element):
        try:
            self._prettify(root_element)
            ET.ElementTree(root_element).write(self.__filename, encoding="utf-8", xml_declaration=True)
            print(f"Data successfully written to file '{self.__filename}'!")
            return True
        except Exception as e:
            raise FileCorruptedError(f"Error writing to file: {str(e)}")

    @logged(mode="console")
    def get_tasks_sorted_by_priority(self):
        try:
            root = self.read()
            all_tasks = root.findall('./task')

            def sort_key(task):
                priority = task.get('priority', 'Low')
                priority_value = XMLFileHandler.PRIORITY_ORDER.get(priority, 99)

                due_date_str = task.findtext('due_date')
                default_date = datetime(9999, 12, 31)

                try:
                    date_value = datetime.strptime(due_date_str, "%Y-%m-%d") if due_date_str else default_date
                except ValueError:
                    date_value = default_date
                
                return (priority_value, date_value)

            return sorted(all_tasks, key=sort_key)
            
        except Exception as e:
            print(f"Unexpected error during sorting: {str(e)}")
            return []

    def display_sorted_tasks(self, tasks):
        print("\n--- Sorted Task List (Priority > Date) ---")
        if not tasks:
            print("Task list is empty.")
            return

        for i, task in enumerate(tasks, 1):
            priority = task.get('priority', 'N/A')
            title = task.findtext('title', 'N/A')
            due_date = task.findtext('due_date', 'N/A')
            print(f"{i:2}. [{priority:6}] | Date: {due_date:10} | {title}")


def create_sample_tasks(root):
    tasks_data = [
        {"id": "101", "priority": "High", "title": "Complete Report", "date": "2025-12-05"},
        {"id": "102", "priority": "Medium", "title": "Reply to Emails", "date": "2025-12-01"},
        {"id": "107", "priority": "High", "title": "Create Backup", "date": "2025-12-02"},
        {"id": "108", "priority": "Low", "title": "Buy Coffee", "date": None}, 
        {"id": "106", "priority": "Medium", "title": "Prepare Presentation", "date": "2025-12-02"},
    ]

    for data in tasks_data:
        task = ET.SubElement(root, "task")
        task.set("id", data["id"])
        task.set("priority", data["priority"])
        ET.SubElement(task, "title").text = data["title"]
        if data["date"]:
            ET.SubElement(task, "due_date").text = data["date"]
        ET.SubElement(task, "status").text = "Pending"
    return root

def main():
    test_filename = "todo_list_short.xml"
    if os.path.exists(test_filename): os.remove(test_filename)
    if os.path.exists("file_operations.log"): os.remove("file_operations.log")
    
    try:
        handler = XMLFileHandler(test_filename)
        handler.create("tasks") 

        root = ET.Element("tasks")
        root = create_sample_tasks(root)
        print("Writing initial UNSORTED data to XML...")
        handler.write(root) 

        sorted_list = handler.get_tasks_sorted_by_priority()

        new_sorted_root = ET.Element("tasks")
        for task_element in sorted_list:
            new_sorted_root.append(task_element)
            
        print("\nOverwriting XML file with SORTED data...")
        handler.write(new_sorted_root) 

        handler.display_sorted_tasks(sorted_list)
        
    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")

if __name__ == "__main__":
    main()