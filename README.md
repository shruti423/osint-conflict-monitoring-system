# OSINT Conflict Monitoring System

**Candidate:** Shruti Bhale  
**Role:** Data Science / Data Modeling Candidate  
**Date:** April 2026  

## Project Overview
This repository contains a lightweight, automated intelligence system designed to monitor open-source information regarding the Iran-US/Israel conflict. 

Rather than a standard CRUD application, this system is engineered with a heavy focus on **Data Science and NLP**. It automatically ingests unstructured text from multiple global sources, extracts key entities, mathematically deduplicates reporting using vector clustering, and flags statistical escalations using anomaly detection algorithms.

## System Architecture
* **Ingestion:** 5 distinct open-source pipelines (NewsAPI, ReliefWeb, GDELT, GNews, RSS).
* **LLM Parsing:** GROQ API for structured entity extraction.
* **Data Science Engine:** Scikit-learn (Isolation Forest), `sentence-transformers` (Clustering), Pandas.
* **Backend:** FastAPI.
* **Frontend:** React (AI-assisted generation).

## Mandatory Documentation
All mandatory documentation requested by the SAIG Hiring Team can be found in the `docs/` folder:
1. `Planning_Note.pdf` 
2. `Architecture_Note.pdf` *(Pending Phase 4)*
3. `Decision_Log.pdf` *(Pending Phase 4)*
4. `Final_Retrospective.pdf` *(Pending Phase 5)*
5. `AI_Usage_Declaration.pdf` *(Pending Phase 5)*

## Local Setup & Reproduction
*(Instructions for running this pipeline locally will be added upon final system compilation).*