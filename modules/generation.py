import io
import random
import xml.etree.ElementTree as ET
import zipfile

from modules.utils import random_str, DEFAULT_ENCODING

CONSTANTS = {
    'max_str_len': 10,
    'level_val': {
        'min': 1,
        'max': 100
    },
    'objects_num': {
        'min': 1,
        'max': 10
    }
}


COMPRESSION_RATE = zipfile.ZIP_STORED


def generate_xml_contents(max_str_len: int = CONSTANTS['max_str_len']) -> bytes:
    root = ET.Element('root')
    id_val_len = random.randint(1, max_str_len)
    id_val = random_str(id_val_len)
    _ = ET.SubElement(
        root,
        'var',
        attrib={
            'name': 'id',
            'value': id_val
        }
    )
    _ = ET.SubElement(
        root,
        'var',
        attrib={
            'name': 'level',
            'value': str(random.randint(
                CONSTANTS['level_val']['min'],
                CONSTANTS['level_val']['max']
            ))
        }
    )
    objects = ET.SubElement(root, 'objects')
    objects_num = random.randint(
        CONSTANTS['objects_num']['min'],
        CONSTANTS['objects_num']['max']
    )
    for _ in range(objects_num):
        _ = ET.SubElement(
            objects,
            'object',
            attrib={
                'name': random_str(max_str_len),
            }
        )

    return ET.tostring(root, encoding=DEFAULT_ENCODING)


def create_xml_file() -> io.BytesIO:
    return io.BytesIO(generate_xml_contents())


def create_zip_file(xmls_num) -> io.BytesIO:
    zip_buffer = io.BytesIO()

    # in-memory zip file creation
    with zipfile.ZipFile(zip_buffer, "a",
                         COMPRESSION_RATE, False) as zip_file:
        for i in range(xmls_num):
            file_name, data = (f'{i}.xml', create_xml_file())
            zip_file.writestr(file_name, data.getvalue())

    return zip_buffer
