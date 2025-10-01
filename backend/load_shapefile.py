import os
import sys
import geopandas as gpd
from sqlalchemy import create_engine, text

# --- Настройки подключения к PostGIS ---
DB_USER = "postgres"
DB_PASS = "postgres"
DB_NAME = "gis"
DB_HOST = "localhost"
DB_PORT = 5432

# Создаём URL подключения
db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url, future=True)  # future=True для SQLAlchemy 2.x

# --- Путь к шейп-файлу ---
shapefile_path = "data/shapefiles/regions.shp"

# Проверка, что файл существует
if not os.path.exists(shapefile_path):
    print(f"Ошибка: файл {shapefile_path} не найден!")
    sys.exit(1)

try:
    # Чтение шейп-файла через GeoPandas
    gdf = gpd.read_file(shapefile_path)
    print(f"Файл {shapefile_path} успешно прочитан. Количество записей: {len(gdf)}")

    # Загрузка в таблицу regions в PostGIS
    # Используем to_postgis с новым параметром engine.connect()
    with engine.begin() as conn:  # автоматический commit/rollback
        gdf.to_postgis('regions', conn, if_exists='replace', index=False)
        print("Данные загружены в таблицу 'regions' успешно!")

        # Проверка количества записей
        result = conn.execute(text("SELECT COUNT(*) FROM regions;"))
        count = result.scalar()
        print(f"В таблице 'regions' теперь {count} записей.")

except Exception as e:
    print("Произошла ошибка при загрузке шейпа:", e)
    sys.exit(1)
