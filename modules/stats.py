import logging
import zipfile
from io import StringIO
from typing import List, Dict, Union
import xml.etree.ElementTree as ET
import re
import csv

from modules.utils import DEFAULT_ENCODING

SEARCH_PATHS = {
    'id': './/*[@name="id"]',
    'level': './/*[@name="level"]',
    'objects': './/objects'
}
XML_TEMPLATE = r".*\.xml"
CSV_PARAMS = {
    'delimiter': ',',
    'quoting': csv.QUOTE_MINIMAL,
}

def get_xml_stats(xml_data: bytes) -> Dict[str, Union[str, List[str]]]:
    """
    Extract required data from XML: var.id, var.level, [object.name, object.name,...]
    and return them in dictionary form:
    :param xml_data:
    :return: {
        "id": "1234",
        "level": "level",
        "object_names": ["123", "def"]
    }
    """

    # probably not obvious. These functions were created to meet strict DRY requirements
    def find_unique_el(_root, el_name) -> ET.Element:
        path = SEARCH_PATHS[el_name]
        found = root.findall(path)
        assert len(found) == 1, f"Too many var elements with '{path}' path"
        return found[0]

    def get_val(el) -> str:
        val = el.get('value')
        if not val:
            assert False, f"Value not found"
        return val

    root = ET.fromstring(xml_data.decode(DEFAULT_ENCODING))

    id = get_val(find_unique_el(root, 'id'))
    level = get_val(find_unique_el(root, 'level'))

    objects = find_unique_el(root, 'objects')
    object_names = [object.get('name') for object in objects]

    return {
        "id": id,
        "level": level,
        "object_names": object_names
    }


def get_zip_stats(zip_fname) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Get stats for every XML file and return them in list
    :param zip_fname:
    :return:
    """
    xml_stats = []
    try:
        with zipfile.ZipFile(zip_fname) as zip_f:
            for zipfile_info in zip_f.filelist:
                logging.debug(f"Processing XML {zipfile_info.filename}")
                if not re.match(XML_TEMPLATE, zipfile_info.filename):
                    logging.error(f"File does not match XML template ({XML_TEMPLATE})")
                    continue
                with zip_f.open(zipfile_info, 'r') as xml_f:
                    xml_stats.append(
                        get_xml_stats(xml_f.read())
                    )
    except zipfile.BadZipFile as e:
        logging.exception(f"Failed to read ZIP contents: {str(e)}")
    except OSError as e:
        logging.exception(f"Failed to read file: {str(e)}")
    except Exception as e:
        logging.exception(f"General error: {str(e)}")

    return xml_stats


def stats_to_csv_data(stats: List[Dict[str, Union[str, List[str]]]]) -> (bytes, bytes):
    """
    Combine gathered stats into two CSV files
    :param stats: Format is same as output of get_zip_stats() fun
    :return: <csv file 1 data (id-level pairs)>, <csv file 2 data (id-object.name)>
    """
    # id-level pairs
    f1 = StringIO()
    writer1 = csv.writer(f1, **CSV_PARAMS)
    writer1.writerow(["ID", "Level"])

    # id-object.name pairs
    f2 = StringIO()
    writer2 = csv.writer(f2, **CSV_PARAMS)
    writer2.writerow(["ID", "Object name"])

    for stat in stats:
        writer1.writerow([stat['id'], stat['level']])
        writer2.writerows([
            [stat['id'], obj_name] for obj_name in stat['object_names']
        ])

    return f1.getvalue().encode(DEFAULT_ENCODING), f2.getvalue().encode(DEFAULT_ENCODING)

if __name__ == '__main__':
    xml = """<root>
  <var name="id" value="12345"/>
  <var name="level" value="50"/>
  <objects>
    <object name="abc"/>
    <object name="def"/>
  </objects>
</root>"""

    xml_data = xml.encode(DEFAULT_ENCODING)
    print(get_xml_stats(xml_data))

    stats = get_zip_stats('/tmp/test-zips-of-xmls/test.zip')

    data1, data2 = stats_to_csv_data(stats)

    with open("1.csv", "wb") as f:
        f.write(data1)

    with open("2.csv", "wb") as f:
        f.write(data2)
