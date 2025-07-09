# crpXo - 全栈加密货币数据分析平台

## 项目简介 Project Overview

CryptoStack 是一个基于 AWS 云构建的全栈加密货币数据分析平台，涵盖数据采集、ETL、数据湖、机器学习和可视化。  
该项目展示了如何构建一个可扩展、高效且自动化的加密货币分析解决方案。

CryptoStack is a full-stack crypto data analysis platform built on AWS, covering data ingestion, ETL, data lake, machine learning, and visualization.  
This project demonstrates how to build a scalable, efficient, and automated crypto analytics solution.

---

## 架构 Architecture

```mermaid
graph TD
    A[数据采集 Data Ingestion] --> B[数据湖 Data Lake (S3)]
    B --> C[ETL (Glue/DBT)]
    C --> D[数据仓库 (Athena/Redshift)]
    D --> E[机器学习 (SageMaker)]
    D --> F[可视化 (QuickSight / Streamlit)]
