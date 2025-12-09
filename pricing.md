# Infrastructure Cost Analysis

This document provides cost estimation for the Cloud AI SaaS application under various scaling scenarios.

## Assumptions

- Cloud Provider: AWS (similar pricing applies to GCP/Azure)
- Region: EU (London)
- Requests per user per day: 10
- Peak traffic: 3x average
- Active hours per day: 8
- Image size average: 500KB
- Response size average: 2KB

## Service Resource Requirements

| Service | CPU | Memory | Instance Type (AWS) |
|---------|-----|--------|---------------------|
| YOLO Service | 1 vCPU | 4GB | t3.medium |
| LLM Service | 2 vCPU | 8GB | t3.large |
| API Gateway | 0.5 vCPU | 1GB | t3.small |
| Postprocessor | 0.25 vCPU | 512MB | t3.micro |
| MongoDB | 0.25 vCPU | 1GB | t3.micro |
| RabbitMQ | 0.25 vCPU | 512MB | t3.micro |

## Cost Components

### C_compute - Compute Costs
- EC2 on-demand pricing (monthly)
- t3.micro: ~$7.59/month
- t3.small: ~$15.18/month
- t3.medium: ~$30.37/month
- t3.large: ~$60.74/month

### C_storage - Storage Costs
- MongoDB (EBS gp3): ~$0.08/GB/month
- Firebase Firestore: $0.18/GB stored + $0.06/100K reads + $0.18/100K writes

### C_network - Network Costs
- Data transfer out: ~$0.09/GB (first 10TB)
- Load Balancer: ~$16.43/month + $0.008/LCU-hour

### C_monitoring - Monitoring Costs
- CloudWatch: ~$0.30/metric/month + $0.01/1000 API calls

---

## Scenario 1: Base Requirements (Stage 8)

**Users:**
- YOLO Service: 100 users
- LLM Service: 100 users  
- RabbitMQ Service: 100,000 users

### Formulas

Let:
- N_yolo = number of YOLO users
- N_llm = number of LLM users
- N_rmq = number of RabbitMQ users
- R = requests per user per day
- F = Firebase constant cost

**Compute Cost:**
```
C_yolo(N) = ceil(N / 50) × $30.37
C_llm(N) = ceil(N / 50) × $60.74
C_gateway(N) = ceil((N_yolo + N_llm) / 200) × $15.18
C_postprocessor(N) = ceil(N_rmq / 50000) × $7.59
C_rabbitmq(N) = ceil(N_rmq / 50000) × $7.59
C_mongodb = $7.59

Total Compute = C_yolo + C_llm + C_gateway + C_postprocessor + C_rabbitmq + C_mongodb
```

**Storage Cost:**
```
Storage_per_user = R × 30 × 2KB = 600KB/user/month
Total_storage = (N_yolo + N_llm) × 600KB / 1024 / 1024 GB

C_mongodb_storage = Total_storage × $0.08
C_firebase = F (constant from Stage 5, approximately $25/month for basic usage)
```

**Network Cost:**
```
Data_in = (N_yolo × R × 30 × 500KB) / 1024 / 1024 GB  # Image uploads
Data_out = ((N_yolo + N_llm) × R × 30 × 2KB) / 1024 / 1024 GB

C_network = Data_out × $0.09 + $16.43 (ALB base)
```

### Calculation for 100 + 100 + 100,000 users

```
C_yolo = ceil(100/50) × $30.37 = 2 × $30.37 = $60.74
C_llm = ceil(100/50) × $60.74 = 2 × $60.74 = $121.48
C_gateway = ceil(200/200) × $15.18 = 1 × $15.18 = $15.18
C_postprocessor = ceil(100000/50000) × $7.59 = 2 × $7.59 = $15.18
C_rabbitmq = ceil(100000/50000) × $7.59 = 2 × $7.59 = $15.18
C_mongodb = $7.59

Total Compute = $235.35/month
```

```
Storage = 200 × 600KB ≈ 0.12GB
C_mongodb_storage = 0.12 × $0.08 ≈ $0.01
C_firebase = F ≈ $25.00
```

```
Data_in = 100 × 10 × 30 × 500KB ≈ 14.3GB
Data_out = 200 × 10 × 30 × 2KB ≈ 0.11GB
C_network = 0.11 × $0.09 + $16.43 ≈ $16.44
```

```
C_monitoring ≈ $11.00
```

### Total for Scenario 1
```
Total = $235.35 + $0.01 + $25.00 + $16.44 + $11.00 + F
Total ≈ $287.80/month + F
```

---

## Scenario 2: 200,000 Concurrent Users

**Distribution assumption:**
- YOLO Service: 80,000 users (40%)
- LLM Service: 80,000 users (40%)
- RabbitMQ Service: 200,000 users (100%)

### Calculation

```
C_yolo = ceil(80000/50) × $30.37 = 1600 × $30.37 = $48,592
C_llm = ceil(80000/50) × $60.74 = 1600 × $60.74 = $97,184
C_gateway = ceil(160000/200) × $15.18 = 800 × $15.18 = $12,144
C_postprocessor = ceil(200000/50000) × $7.59 = 4 × $7.59 = $30.36
C_rabbitmq = ceil(200000/50000) × $7.59 = 4 × $7.59 = $30.36
C_mongodb (cluster) = 3 × $30.37 = $91.11

Total Compute ≈ $158,072/month
```

```
Storage = 160000 × 600KB ≈ 91.55GB
C_mongodb_storage = 91.55 × $0.08 = $7.32
C_firebase = F × 800 (scaled) ≈ $2,000
```

```
Data_in = 80000 × 10 × 30 × 500KB ≈ 11,444GB
Data_out = 160000 × 10 × 30 × 2KB ≈ 91.55GB
C_network = 91.55 × $0.09 + $16.43 × 4 (multiple ALBs) ≈ $73.98
C_data_in = 11,444 × $0.00 (inbound free) = $0
```

```
C_monitoring = 50 metrics × $0.30 × 12 services ≈ $180
```

### Total for Scenario 2
```
Total = $158,072 + $7.32 + $2,000 + $73.98 + $180
Total ≈ $160,333/month
```

---

## Cost Optimization Strategies

### 1. Reserved Instances (1-year commitment)
- Savings: ~40%
- New total for 200K users: ~$96,200/month

### 2. Spot Instances for Non-Critical Workloads
- Postprocessor can use spot instances
- Savings: ~70% on those instances

### 3. Auto-scaling
```
Instances = max(min_instances, ceil(current_load / capacity_per_instance))
```
- Scale down during off-peak hours
- Potential savings: 30-50% on compute

### 4. Container Orchestration (EKS/ECS)
- Better resource utilization
- Bin-packing efficiency
- Estimated savings: 20-30%

---

## Summary Table

| Scenario | Users | Monthly Cost |
|----------|-------|--------------|
| Base (Stage 8) | 100 + 100 + 100K | ~$288 + F |
| Scaled (200K) | 80K + 80K + 200K | ~$160,333 |
| Scaled + Reserved | 80K + 80K + 200K | ~$96,200 |
| Scaled + Optimized | 80K + 80K + 200K | ~$80,000 |

---

## Cost Per User Analysis

| Scenario | Cost/User/Month |
|----------|-----------------|
| Base | $1.44 |
| Scaled | $0.80 |
| Optimized | $0.40 |

---

## References

1. AWS EC2 Pricing: https://aws.amazon.com/ec2/pricing/
2. AWS EBS Pricing: https://aws.amazon.com/ebs/pricing/
3. Firebase Pricing: https://firebase.google.com/pricing
4. AWS Data Transfer Pricing: https://aws.amazon.com/ec2/pricing/on-demand/#Data_Transfer
