# -*- coding: utf-8 -*-
"""
@Description:
@Author: sli229
"""

import logging
import pathlib
from typing import Tuple
import sqlalchemy
from shapely.geometry import Polygon

import geopandas as gpd
import geoapis.vector

from src import config
from src.digitaltwin import setup_environment

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(levelname)s:%(asctime)s:%(name)s:%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

log.addHandler(stream_handler)


def catchment_area_geometry_info(catchment_file: pathlib.Path) -> Polygon:
    """
    Extract shapely geometry polygon from the catchment file.

    Parameters
    ----------
    catchment_file : pathlib.Path
        The file path of the catchment polygon shapefile.
    """
    catchment = gpd.read_file(catchment_file)
    catchment = catchment.to_crs(2193)
    catchment_polygon = catchment["geometry"][0]
    return catchment_polygon


def get_catchment_centroid_coords(catchment_file: pathlib.Path) -> Tuple[float, float]:
    """
    Extract the catchment polygon centroid coordinates.

    Parameters
    ----------
    catchment_file : pathlib.Path
        The file path for the catchment polygon.
    """
    catchment_polygon = catchment_area_geometry_info(catchment_file)
    long, lat = catchment_polygon.centroid.coords[0]
    return lat, long


def get_stats_nz_dataset(key: str, layer_id: int) -> gpd.GeoDataFrame:
    vector_fetcher = geoapis.vector.StatsNz(key, verbose=True, crs=2193)
    response_data = vector_fetcher.run(layer_id)
    return response_data


def get_regional_council_clipped(key: str, layer_id: int) -> gpd.GeoDataFrame:
    regional_clipped = get_stats_nz_dataset(key, layer_id)
    regional_clipped.columns = regional_clipped.columns.str.lower()
    # move geometry column to last column
    regional_clipped = regional_clipped.drop(columns=['geometry'], axis=1).assign(geometry=regional_clipped['geometry'])
    regional_clipped = gpd.GeoDataFrame(regional_clipped)
    return regional_clipped


def check_table_exists(engine, db_table_name: str) -> bool:
    """
    Check if table exists in the database.

    Parameters
    ----------
    engine
        Engine used to connect to the database.
    db_table_name : str
        Database table name.
    """
    insp = sqlalchemy.inspect(engine)
    table_exists = insp.has_table(db_table_name, schema="public")
    return table_exists


def regional_council_clipped_to_db(engine, key: str, layer_id: int):
    if check_table_exists(engine, "region_geometry_clipped"):
        log.info("Table 'region_geometry_clipped' already exists in the database.")
    else:
        regional_clipped = get_regional_council_clipped(key, layer_id)
        regional_clipped.to_postgis("region_geometry_clipped", engine, index=False, if_exists="replace")
        log.info(f"Added regional council clipped (StatsNZ {layer_id}) data to database.")


def main():
    # Get StatsNZ api key
    stats_nz_api_key = config.get_env_variable("StatsNZ_API_KEY")
    # Connect to the database
    engine = setup_environment.get_database()
    # Catchment polygon
    catchment_file = pathlib.Path(r"selected_polygon.geojson")
    catchment_polygon = catchment_area_geometry_info(catchment_file)
    # Store regional council clipped data in the database
    regional_council_clipped_to_db(engine, stats_nz_api_key, 111181)


if __name__ == "__main__":
    main()
