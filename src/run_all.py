import logging

from src.digitaltwin import get_data_from_db, run
from src.dynamic_boundary_conditions import main_rainfall, main_tide_slr
from src.lidar import lidar_metadata_in_db
from src.flood_model import bg_flood_model

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(levelname)s:%(asctime)s:%(name)s:%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)

if __name__ == '__main__':
    log.debug("run.main()")
    run.main()
    log.debug("get_data_from_db.main()")
    get_data_from_db.main()
    log.debug("lidar_metadata_in_db.main()")
    lidar_metadata_in_db.main()
    log.debug("main_rainfall.main()")
    main_rainfall.main()
    try:
        log.debug("main_tide_slr.main()")
        main_tide_slr.main()
    except SystemExit:
        pass
    log.debug("bg_flood_model.main()")
    bg_flood_model.main()
