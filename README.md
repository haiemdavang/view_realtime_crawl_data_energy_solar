# ElectricityMaps-LA-Analysis

Real-time monitoring and analysis of electricity source intensity for the Los Angeles power grid using the Electricitymaps API.

### Real-time Dashboard

![Dashboard Overview](docs/images/dashboard-overview.png)
_Main dashboard showing real-time power generation, grid state, solar input, and prediction cluster_

### Power Generation & Solar Forecast

![Power Generation Sources](docs/images/power-generation.png)
_Live power generation by source (Solar, Wind, Gas, Hydro) with 24-hour solar forecast_

### Analysis & Correlations

![Analysis Dashboard](docs/images/analysis-view.png)
_Load trend analysis, daily seasonality profile, source correlation matrix, and load distribution_

### Detailed Analytics

![Detailed Analytics](docs/images/detailed-analytics.png)
_In-depth view of trend analysis, seasonal patterns, and clustering visualization_

## 📋 Overview

This project provides a comprehensive solution for monitoring, analyzing, and predicting electricity grid data for Los Angeles. It includes:

- **Data Ingestion**: Real-time and historical data collection from ElectricityMaps API
- **Data Analysis**: Trend analysis, seasonal decomposition, and correlation analysis
- **ML Prediction**: Solar energy forecasting using deep learning models
- **Clustering**: Pattern recognition in energy consumption
- **Visualization Dashboard**: Real-time monitoring interface

## 🏗️ Architecture

```
.
├── backend/
│   ├── clustering/         # K-Means clustering service
│   ├── data_analysis/      # Statistical analysis service
│   ├── prediction/         # ML prediction service (TensorFlow)
│   └── ingestion/          # Data collection service
├── ec2/
│   ├── api/               # FastAPI backend server
│   └── frontend/          # React dashboard (Vite + TypeScript)
└── docker-compose.yml     # Container orchestration
```

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- AWS Account (for Lambda deployment)
- ElectricityMaps API Token
- PostgreSQL database

### Environment Configuration

#### 1. Backend Services (Lambda Functions)

Each backend service requires the following environment variables:

```bash
# Database Configuration
DB_HOST=your-database-host.rds.amazonaws.com
DB_NAME=electricity_db
DB_USER=postgres
DB_PASS=your-secure-password

# ElectricityMaps API (for ingestion service only)
AUTH_TOKEN=your-electricitymaps-api-token
ZONE=US-CAL-LDWP
HISTORY_DAYS=30
```

**Configure in AWS Lambda:**

- Go to Lambda Console → Select Function → Configuration → Environment Variables
- Add each variable as shown above

#### 2. EC2 API Service

Create `ec2/.env` file:

```bash
# Database Configuration
DB_HOST=your-database-host.rds.amazonaws.com
DB_NAME=electricity_db
DB_USER=postgres
DB_PASS=your-secure-password
DB_PORT=5432

# AWS Configuration
AWS_REGION=ap-southeast-1

# Lambda Function Names
INGESTION_LAMBDA=ingestion-lambda
ANALYSIS_LAMBDA=analysis-lambda
PREDICTION_LAMBDA=prediction-lambda
CLUSTERING_LAMBDA=clustering-lambda

# API Configuration
CLUSTERING_SERVICE_URL=http://clustering-service:8001
```

#### 3. Frontend Service

The frontend reads the API URL from environment variables:

```bash
# ec2/frontend/.env (create this file)
VITE_API_URL=http://your-api-server:8000
```

For production deployment:

```bash
VITE_API_URL=http://52.77.236.120:8000
```

### 🐳 Docker Deployment (EC2)

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ElectricityMaps-LA-Analysis/ec2
   ```

2. **Configure environment files**

   ```bash
   # Copy example and edit with your credentials
   cp .env.example .env
   nano .env
   ```

3. **Build and start services**

   ```bash
   docker-compose up -d --build
   ```

4. **Verify services**

   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

### ☁️ Lambda Deployment

#### Build Docker Images

```bash
# Navigate to each backend service
cd backend/ingestion
docker build -t ingestion-lambda .

cd ../data_analysis
docker build -t analysis-lambda .

cd ../prediction
docker build -t prediction-lambda .

cd ../clustering
docker build -t clustering-lambda .
```

#### Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com

# Tag and push each image
docker tag ingestion-lambda:latest <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/ingestion-lambda:latest
docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/ingestion-lambda:latest

# Repeat for other services...
```

#### Configure Lambda Functions

1. Create Lambda functions in AWS Console
2. Set container image from ECR
3. Configure environment variables (see section above)
4. Set timeout: 5 minutes
5. Set memory: 512MB - 1024MB
6. Add EventBridge triggers for scheduling

## 📊 Database Schema

The application uses PostgreSQL with the following main tables:

- `electricity_measurements`: Raw measurement data
- `electricity_analysis_results`: Processed analysis results
- `solar_predictions`: 24-hour solar forecasts
- `electricity_correlations`: Feature correlation matrix

## 🔧 API Endpoints

### Data Retrieval

- `GET /measurements?range={day|week|month}` - Get historical measurements
- `GET /predictions` - Get 24-hour solar forecast
- `GET /status/latest` - Get current grid status
- `GET /clustering?range={day|week|month}` - Get clustering results

### Analysis

- `GET /analysis/trend?range={week|month|year}` - Trend analysis
- `GET /analysis/seasonal?range={week|month|year}` - Seasonal patterns
- `GET /analysis/correlations` - Correlation matrix

### Service Triggers

- `POST /trigger-ingestion` - Trigger data collection
- `POST /trigger-analysis` - Trigger statistical analysis
- `POST /trigger-prediction` - Trigger ML forecasting
- `POST /trigger-clustering` - Trigger pattern clustering

## 📈 Features

### Real-time Monitoring

- Live electricity generation by source (Solar, Wind, Gas, Hydro)
- Carbon intensity tracking
- Power consumption trends

### Advanced Analytics

- **Trend Analysis**: Long-term patterns in energy generation
- **Seasonal Decomposition**: Daily/hourly consumption patterns
- **Correlation Analysis**: Relationships between energy sources

### Machine Learning

- **Solar Forecasting**: 24-hour predictions using MLP neural network
- **Pattern Clustering**: K-Means clustering of consumption patterns
- **Anomaly Detection**: Identifies unusual consumption patterns

### Interactive Dashboard

- Real-time charts and visualizations
- Time range selection (Day/Week/Month)
- Cluster visualization
- Prediction confidence intervals

## 🛠️ Technology Stack

**Backend:**

- Python 3.11/3.12
- TensorFlow 2.20 (Prediction)
- scikit-learn (Analysis & Clustering)
- FastAPI (API Server)
- PostgreSQL (Database)

**Frontend:**

- React 18 + TypeScript
- Vite (Build Tool)
- Recharts (Visualization)
- Tailwind CSS (Styling)
- Axios (HTTP Client)

**Infrastructure:**

- AWS Lambda (Serverless Compute)
- AWS RDS (PostgreSQL)
- AWS ECR (Container Registry)
- Docker (Containerization)

## 📝 Usage Examples

### Trigger Manual Data Ingestion

```bash
curl -X POST http://localhost:8000/trigger-ingestion \
  -H "Content-Type: application/json" \
  -d '{"action": "backfill", "start_date": "2025-01-01"}'
```

### Get Solar Predictions

```bash
curl http://localhost:8000/predictions
```

### Get Clustering Results

```bash
curl "http://localhost:8000/clustering?range=week"
```

## 🔍 Monitoring & Logs

**Docker Logs:**

```bash
# View all services
docker-compose logs -f

# View specific service
docker-compose logs -f api-service
docker-compose logs -f frontend
```

**Lambda Logs:**

- View in AWS CloudWatch Logs
- Log groups: `/aws/lambda/ingestion-lambda`, etc.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Data provided by [ElectricityMaps API](https://www.electricitymaps.com/)
- Los Angeles Department of Water and Power (LADWP) for grid data

## 📞 Support

For issues and questions:

- Open an issue on GitHub
- Check the [API Documentation](http://localhost:8000/docs)
- Review CloudWatch logs for Lambda functions
