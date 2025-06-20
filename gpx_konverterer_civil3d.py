
import streamlit as st
import xml.etree.ElementTree as ET
from io import StringIO
from pyproj import Transformer
import pandas as pd

transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)

st.title("GPX til KOFormat (Civil 3D)")
st.write("Last opp en GPX-fil med waypoints. Appen konverterer koordinatene til ETRS89 UTM sone 32 og lar deg laste ned resultatet i KOFormat for Civil 3D.")

uploaded_file = st.file_uploader("Velg en GPX-fil", type=["gpx", "xml"])

if uploaded_file is not None:
    gpx_content = uploaded_file.read().decode("utf-8")
    tree = ET.parse(StringIO(gpx_content))
    root = tree.getroot()

    ns = {"default": "http://www.topografix.com/GPX/1/1"}
    data = []

    for wpt in root.findall("default:wpt", ns):
        lat = float(wpt.attrib["lat"])
        lon = float(wpt.attrib["lon"])
        name_elem = wpt.find("default:name", ns)
        type_elem = wpt.find("default:type", ns)
        ele_elem = wpt.find("default:ele", ns)

        name = name_elem.text.strip() if name_elem is not None else ""
        type_ = type_elem.text.strip() if type_elem is not None else ""
        full_name = f"{name} {type_}".strip()

        z = float(ele_elem.text.strip()) if ele_elem is not None else 0.0
        utm_x, utm_y = transformer.transform(lon, lat)

        data.append({
            "Navn": full_name,
            "UTM_X": round(utm_x, 3),
            "UTM_Y": round(utm_y, 3),
            "Z": round(z, 3)
        })

    if data:
        df = pd.DataFrame(data)
        st.success(f"Fant {len(df)} waypoints.")
        st.dataframe(df)

        kof_lines = [
            f"05 {row['Navn']:<20}{row['UTM_Y']:10.3f}  {row['UTM_X']:10.3f}  {row['Z']:7.3f}"
            for _, row in df.iterrows()
        ]
        kof_content = "\n".join(kof_lines)

        st.download_button(
            label="Last ned KOFormat-fil (Civil 3D)",
            data=kof_content,
            file_name="konvertert_civil3d.kof",
            mime="text/plain"
        )
    else:
        st.warning("Fant ingen waypoints i GPX-filen.")
