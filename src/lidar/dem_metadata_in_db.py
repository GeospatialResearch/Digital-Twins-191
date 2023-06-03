# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 13:22:27 2021.

@author: pkh35, sli229
"""

import logging
import pathlib
from datetime import datetime
from typing import Tuple, Dict, Any

import geopandas as gpd
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

import geofabrics.processor

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(levelname)s:%(asctime)s:%(name)s:%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

log.addHandler(stream_handler)

Base = declarative_base()


class HydroDEM(Base):
    """Class used to create 'hydrological_dem' table."""
    __tablename__ = "hydrological_dem"
    unique_id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.now(), comment="output created datetime")
    geometry = Column(Geometry("GEOMETRY", srid=2193), comment="catchment area coverage")


def create_hydro_dem_table(engine: Engine) -> None:
    """Create 'hydrological_dem' table in the database if it doesn't exist."""
    HydroDEM.__table__.create(bind=engine, checkfirst=True)


def get_hydro_dem_metadata(
        instructions: Dict[str, Any],
        catchment_boundary: gpd.GeoDataFrame) -> Tuple[str, str, str]:
    """Get the hydrological DEM metadat~a."""
    data_paths: Dict[str, Any] = instructions["instructions"]["data_paths"]
    result_dem_path = pathlib.Path(data_paths["local_cache"]) / data_paths["subfolder"] / data_paths["result_dem"]
    hydro_dem_name = result_dem_path.name
    hydro_dem_path = result_dem_path.as_posix()
    geometry = catchment_boundary["geometry"].to_wkt().iloc[0]
    return hydro_dem_name, hydro_dem_path, geometry


def store_hydro_dem_metadata_to_db(
        engine: Engine,
        instructions: Dict[str, Any],
        catchment_boundary: gpd.GeoDataFrame) -> None:
    """Store metadata of the hydrologically conditioned DEM in the database."""
    create_hydro_dem_table(engine)
    hydro_dem_name, hydro_dem_path, geometry = get_hydro_dem_metadata(instructions, catchment_boundary)
    with Session(engine) as session:
        hydro_dem = HydroDEM(file_name=hydro_dem_name, file_path=hydro_dem_path, geometry=geometry)
        session.add(hydro_dem)
        session.commit()
        log.info("Hydro DEM metadata stored successfully in the database.")


def check_hydro_dem_exist(engine: Engine, catchment_boundary: gpd.GeoDataFrame) -> bool:
    """Check if hydro DEM already exists in the database for the catchment area."""
    create_hydro_dem_table(engine)
    geometry = catchment_boundary["geometry"].to_wkt().iloc[0]
    query = f"SELECT EXISTS (SELECT 1 FROM hydrological_dem WHERE geometry = '{geometry}');"
    return engine.execute(query).scalar()


def run_geofabrics_hydro_dem(instructions: Dict[str, Any]) -> None:
    """Use geofabrics to generate the hydrologically conditioned DEM."""
    runner = geofabrics.processor.RawLidarDemGenerator(instructions["instructions"])
    runner.run()
    runner = geofabrics.processor.HydrologicDemGenerator(instructions["instructions"])
    runner.run()


def dem_metadata_from_db(selected_polygon: gpd.GeoDataFrame, engine: Engine):
    """Get requested dem information from the database."""
    geometry = str(selected_polygon["geometry"][0])
    query = f"SELECT filepath FROM hydrological_dem WHERE geometry = '{geometry}'"
    dem = engine.execute(query)
    return dem.fetchone()[0]


def generate_hydro_dem(
        engine: Engine,
        instructions: Dict[str, Any],
        catchment_boundary: gpd.GeoDataFrame):
    """Pass dem information to other functions."""
    if not check_hydro_dem_exist(engine, catchment_boundary):
        run_geofabrics_hydro_dem(instructions)
        store_hydro_dem_metadata_to_db(engine, instructions, catchment_boundary)
    dem_filepath = dem_metadata_from_db(catchment_boundary, engine)
    return dem_filepath
