import os

from pyspark.sql import SparkSession

if __name__ == "__main__":
    spark = (
        SparkSession.builder.appName("ReadFromS3AndOracle")
        # Oracle setup
        .config("spark.jars", "/opt/spark/jars/ojdbc8.jar")
        .config("spark.driver.extraClassPath", "/opt/spark/jars/ojdbc8.jar")
        # S3 setup
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem",
        )
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("S3_ACCESS_KEY"))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("S3_SECRET_KEY"))
        .config("spark.hadoop.fs.s3a.endpoint", os.getenv("S3_ENDPOINT_URL"))
        # S3 hacks
        .config("spark.hadoop.fs.s3a.fast.upload", "true")
        .config("spark.hadoop.fs.s3a.experimental.input.fadvise", "random")
        .getOrCreate()
    )

    S3_FILE_PATH = "dummy/industry.csv"
    S3_FULL_FILE_PATH = f"s3a://{os.getenv('S3_BUCKET_NAME')}/{S3_FILE_PATH}"
    SQL_QUERY = "(SELECT * FROM ALEX.ONS_MED_ITEM where ID_MI < 50) tmp"

    user = os.getenv("ORACLE_USERNAME")
    password = os.getenv("ORACLE_PASSWORD")
    host = os.getenv("ORACLE_HOST")
    db = os.getenv("ORACLE_DB")
    jdbcUrl = f"jdbc:oracle:thin:@{host}:{db}"

    # Get the log4j logger
    log4jLogger = spark._jvm.org.apache.log4j
    logger = log4jLogger.LogManager.getLogger(os.getenv("LOGGER_NAME"))

    try:
        jdbcDF = (
            spark.read.format("jdbc")
            .option("url", jdbcUrl)
            .option("driver", "oracle.jdbc.driver.OracleDriver")
            .option("oracle.jdbc.timezoneAsRegion", "false")
            .option("dbtable", SQL_QUERY)
            .option("user", user)
            .option("password", password)
            .load()
        )
        jdbcDF.show(10, 0)
        logger.info("Content of the table from oracle loaded and showed.")

        df = spark.read.csv(S3_FULL_FILE_PATH, header=True)
        df.show(10, 0)
        logger.info("Content of the table from s3 loaded and showed.")
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error(e)
    finally:
        spark.stop()
        logger.info("Spark session stopped.")
