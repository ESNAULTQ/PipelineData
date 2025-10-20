from sqlmodel import SQLModel, Field

class YellowTaxiTrip(SQLModel,table=True):
    id SERIAL PRIMARY KEY,
                vendorid INTEGER,
                tpep_pickup_datetime TIMESTAMP,
                tpep_dropoff_datetime TIMESTAMP,
                passenger_count DOUBLE PRECISION,
                trip_distance DOUBLE PRECISION,
                ratecodeid DOUBLE PRECISION,
                store_and_fwd_flag VARCHAR(1),
                pulocationid INTEGER,
                dolocationid INTEGER,
                payment_type INTEGER,
                fare_amount DOUBLE PRECISION,
                extra DOUBLE PRECISION,
                mta_tax DOUBLE PRECISION,
                tip_amount DOUBLE PRECISION,
                tolls_amount DOUBLE PRECISION,
                improvement_surcharge DOUBLE PRECISION,
                total_amount DOUBLE PRECISION,
                congestion_surcharge DOUBLE PRECISION,
                airport_fee DOUBLE PRECISION,
                cbd_congestion_fee DOUBLE PRECISION