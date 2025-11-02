# Research: Free Hosting with 32GB RAM

## Executive Summary

After thorough research of cloud hosting options in 2024-2025, **no major cloud provider offers an always-free tier with 32GB of RAM**. Free tiers are designed for learning, prototyping, and small workloads, typically providing 1-2GB of RAM at most.

This document outlines the available options, alternatives, and recommendations for obtaining high-memory hosting for the Jadlo project.

---

## 1. Major Cloud Provider Free Tiers

### 1.1 Oracle Cloud (Most Generous)

**Oracle Cloud Infrastructure Always Free Tier** is the closest to high-memory free hosting:

- **ARM-based VMs (Ampere A1)**: Up to 4 instances totaling **24GB RAM** (free forever)
- **AMD-based VMs**: 2 instances with 1GB RAM each
- **Architecture**: ARM (not x86_64)
- **Best for**: Development, testing, lightweight production workloads

**Limitations**:
- Maximum 24GB RAM, not 32GB
- ARM architecture may require code adjustments
- Limited to specific regions

**References**:
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [Oracle Cloud Free Tier Documentation](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)

### 1.2 AWS Free Tier

**Amazon Web Services Free Tier**:

- **t2.micro/t3.micro instances**: 1 vCPU, **1GB RAM**
- **Duration**: 12 months for new accounts
- **Eligibility**: 750 hours/month

**Limitations**:
- Only 1GB RAM (far from 32GB requirement)
- Time-limited (12 months)
- High-memory instances (e.g., m6i.8xlarge with 32GB) are paid only

**References**:
- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)

### 1.3 Google Cloud Platform

**GCP Free Tier**:

- **e2-micro VM**: 2 vCPUs, **1GB RAM**
- **Duration**: Always free with monthly usage limits
- **Region**: US regions only

**Limitations**:
- Only 1GB RAM
- Geographic restrictions

**References**:
- [Google Cloud Free Tier](https://cloud.google.com/free)
- [GCP Free Tier Details](https://cloud.google.com/free/docs/free-cloud-features)

### 1.4 Microsoft Azure

**Azure Free Account**:

- **B1S VM**: **1GB RAM**
- **Duration**: $200 credit for first 30 days, then limited free services
- **Eligibility**: New accounts

**Limitations**:
- Only 1GB RAM for always-free services
- Trial credits expire after 30 days

**References**:
- [Azure Free Account](https://azure.microsoft.com/en-us/free/)
- [Azure Free Services](https://azure.microsoft.com/en-us/pricing/free-services/)

### 1.5 GitHub Codespaces

**GitHub Codespaces**:

- **Free tier**: 60 core-hours/month for personal accounts
- **Configurations**: 2-core/4GB or 4-core/8GB
- **Best for**: Development environments

**Limitations**:
- Maximum 8GB RAM on free tier
- Limited hours per month
- Not suitable for production hosting

**References**:
- [GitHub Codespaces](https://github.com/features/codespaces)
- [Codespaces Billing](https://docs.github.com/en/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces)

---

## 2. Academic and Research Cloud Credits

For academic institutions and research projects, cloud providers offer substantial credits that can provide access to high-memory instances:

### 2.1 Google Cloud Research Credits

- **Award**: Up to **$5,000+ per proposal**
- **Eligibility**: Faculty, postdocs, PhD students at recognized institutions
- **Instance options**: Up to 624GB RAM (n2-highmem instances)
- **Duration**: Typically 1 year
- **Application**: Research proposal required

**Best for**: AI/ML research, large-scale data processing, computational science

**References**:
- [Google Cloud for Researchers](https://cloud.google.com/edu/researchers)
- [Apply for Research Credits](https://edu.google.com/intl/ALL_us/programs/credits/research/)

### 2.2 AWS Cloud Credit for Research

- **Award**: 
  - Students: Up to $5,000
  - Faculty/Staff: No hard cap (project-based)
- **Eligibility**: Academic institutions, research projects
- **Instance options**: Up to 768GB RAM (x1e/HighMem instances)
- **Application**: Merit-based research proposal

**Best for**: Computational research, genomics, machine learning

**References**:
- [AWS Cloud Credit for Research](https://aws.amazon.com/government-education/research-and-technical-computing/cloud-credit-for-research/)
- [AWS Education Programs](https://aws.amazon.com/grants/)

### 2.3 Microsoft Azure Research Credits

- **Award**: Varies by project, typically $5,000-$10,000+
- **Eligibility**: Faculty, researchers at academic institutions
- **Instance options**: Up to 448GB RAM (E64ds_v4 instances)
- **Application**: Research proposal with scientific impact

**Best for**: High-performance computing, simulation, interdisciplinary research

**References**:
- [Azure Research Credits](https://www.microsoft.com/en-us/azure-academic-research/)
- [Azure for Research](https://www.microsoft.com/en-us/research/academic-program/microsoft-azure-for-research/)

### 2.4 University-Specific Programs

Many universities have dedicated programs:

- **Stanford HAI Google Cloud Credit Grants**: Up to $100,000 for AI research
- **MIT Major Cloud Provider Credits Program**: Various cloud credits for research
- **UW eScience Institute**: AWS and Azure credits for data science

**Application**: Usually restricted to institution members

---

## 3. Edge Computing and Serverless Options

### 3.1 Cloudflare Workers

- **Free tier**: 100,000 requests/day (~3M/month)
- **Memory**: **128MB per invocation**
- **Edge locations**: 300+ globally
- **Best for**: APIs, lightweight compute, edge functions

**Limitations**:
- Only 128MB memory (not suitable for memory-intensive routing)
- Not appropriate for Jadlo's OSMnx-based routing

**References**:
- [Cloudflare Workers](https://workers.cloudflare.com/)
- [Workers Pricing](https://developers.cloudflare.com/workers/platform/pricing/)

### 3.2 Netlify and Vercel

Similar serverless platforms with **128MB memory limits** per function. Not suitable for high-memory workloads like OSMnx routing.

---

## 4. Comparison Table

| Provider          | Free Tier RAM | Academic Credits | Max RAM with Credits | Suitable for Jadlo? |
|-------------------|---------------|------------------|---------------------|---------------------|
| Oracle Cloud      | 24GB (ARM)    | $300 trial       | 24GB                | Limited (ARM)       |
| AWS               | 1GB           | $5,000+          | 768GB               | Yes (with credits)  |
| Google Cloud      | 1GB           | $5,000+          | 624GB               | Yes (with credits)  |
| Azure             | 1GB           | $5,000-$10,000+  | 448GB               | Yes (with credits)  |
| GitHub Codespaces | 8GB           | N/A              | 8GB                 | No (development only)|
| Cloudflare Workers| 128MB         | N/A              | 128MB               | No (too limited)    |
| Netlify/Vercel    | 128MB         | N/A              | 128MB               | No (too limited)    |

### Occasional Use Pricing (32GB RAM, 2-10 Times per Month)

| Provider    | Instance Type | On-Demand (2 uses) | On-Demand (10 uses) | Spot (2 uses) | Spot (10 uses) |
|-------------|--------------|-------------------|---------------------|---------------|----------------|
| AWS         | m6i.2xlarge  | ~$6/month         | ~$31/month          | ~$1.60/month  | ~$8/month      |
| Google Cloud| N2 standard  | ~$6/month         | ~$31/month          | ~$1.50/month  | ~$10/month     |
| Azure       | D8s v3       | ~$6/month         | ~$31/month          | ~$2/month     | ~$10/month     |

*Assumes 8 hours per use. Billing is per-second (AWS/GCP) or per-minute (Azure).*

---

## 5. Why 32GB RAM is Not Available for Free

### 5.1 Cost Considerations

- **Hardware costs**: High-memory servers are expensive to provision and maintain
- **Fair usage**: Free tiers target learning and small workloads
- **Business model**: Cloud providers use free tiers for customer acquisition, not production hosting

### 5.2 Typical Free Tier Philosophy

Free tiers are designed for:
- Learning and experimentation
- Proof-of-concept development
- Small personal projects
- Evaluation before paid commitment

High-resource workloads (32GB+ RAM) are considered production-grade and require paid plans.

---

## 6. Alternatives and Workarounds

### 6.1 Memory Optimization for Current Free Tiers

For the Jadlo project specifically:

1. **Use segmented routing** (already implemented):
   - `scripts/run_poc_segmented.py` splits routes into smaller segments
   - Each segment uses less memory
   - Suitable for Render.com free tier

2. **Intersection-based routing** (experimental):
   - `compute_route_intersections()` reduces memory usage
   - Simplifies graph to intersection nodes only
   - Good for constrained environments

3. **Caching strategies**:
   - Cache OSMnx data to reduce repeated downloads
   - Store frequently-used route segments

### 6.2 Trial Credits

Most cloud providers offer substantial trial credits for new accounts:

- **AWS**: $200-$300 in credits (various programs)
- **Google Cloud**: $300 credit for 90 days
- **Azure**: $200 credit for 30 days
- **Oracle**: $300 credit for 30 days

**Note**: These are temporary and require credit card verification.

### 6.3 Spot/Preemptible Instances

For non-critical workloads:
- **AWS Spot Instances**: Up to 90% discount, but can be terminated
- **Google Preemptible VMs**: Up to 80% discount
- **Azure Spot VMs**: Significant discounts

**Trade-off**: Lower cost but no uptime guarantee.

### 6.4 Occasional Use (2-10 Times per Month)

**Perfect for intermittent workloads** - Pay only when you use resources:

#### On-Demand Instances (Best for Reliability)

Pay-as-you-go pricing with no commitment:

**AWS EC2** (e.g., m6i.2xlarge: 8 vCPUs, 32GB RAM):
- **Hourly rate**: ~$0.38/hour (US East region)
- **2 uses/month** (8 hours each): 16 hours × $0.38 = **~$6/month**
- **10 uses/month** (8 hours each): 80 hours × $0.38 = **~$31/month**

**Google Cloud** (N2 standard with 32GB):
- **Hourly rate**: ~$0.38/hour
- **Similar costs**: $6-$31/month for occasional use

**Azure** (Standard D8s v3: 8 vCPUs, 32GB):
- **Hourly rate**: ~$0.38/hour
- **Comparable pricing** to AWS/GCP

**Advantages**:
- Start/stop as needed - pay only for actual usage
- No interruptions or termination risk
- Billing by the second (AWS/GCP) or minute (Azure)
- Perfect for scheduled batch processing

#### Spot Instances (Best for Cost Savings)

Up to 90% discount on on-demand prices:

**AWS Spot Instances**:
- **Typical rate**: $0.07-$0.15/hour (60-90% discount)
- **2 uses/month**: 16 hours × $0.10 = **~$1.60/month**
- **10 uses/month**: 80 hours × $0.10 = **~$8/month**

**Google Cloud Spot VMs**:
- **Rate**: ~$0.12/hour (region dependent)
- **Cost**: $1.50-$10/month for occasional use

**Azure Spot VMs**:
- Similar savings to AWS/GCP
- Dynamic pricing based on available capacity

**Trade-offs**:
- Can be interrupted with 2-minute (AWS) or 30-second (GCP) notice
- Best for fault-tolerant batch jobs
- Not suitable if interruption is problematic
- Requires automation to handle interruptions

#### Serverless Containers (Alternative for <16GB)

For workloads that can fit in lower memory:

**AWS Fargate** (ECS/EKS):
- Pay per vCPU/GB-second
- Up to 30GB RAM per task
- No server management

**Google Cloud Run**:
- Up to 32GB RAM per container (recently increased)
- Pay only during request processing
- Scales to zero when idle

**Azure Container Apps**:
- Up to 4 vCPUs, 8GB RAM per container
- Pay-per-use pricing

**Note**: For Jadlo's OSMnx routing, traditional VMs are recommended due to memory requirements and startup time.

#### Cost Comparison Table (2-10 Uses/Month)

| Solution | Usage Pattern | Est. Monthly Cost | Reliability | Best For |
|----------|--------------|-------------------|-------------|----------|
| On-Demand | 2 uses × 8h | ~$6 | High | Critical jobs |
| On-Demand | 10 uses × 8h | ~$31 | High | Regular processing |
| Spot | 2 uses × 8h | ~$1.60 | Medium | Batch jobs |
| Spot | 10 uses × 8h | ~$8 | Medium | Fault-tolerant tasks |
| Cloud Run | 2 uses × 8h | Varies | High | Web services |

#### Recommendations for Occasional Use

1. **For critical route generation** (must complete):
   - Use on-demand instances: ~$6-$31/month
   - Simple to use: start instance, run job, stop instance
   - No interruption risk

2. **For cost optimization** (can tolerate interruptions):
   - Use spot instances: ~$1.60-$8/month
   - 60-90% cost savings
   - Implement interruption handling

3. **Automation tips**:
   - Use AWS Lambda/Cloud Functions to start/stop instances
   - Schedule instances with Cloud Scheduler
   - Auto-shutdown after job completion
   - Use instance templates for quick deployment

4. **Billing optimization**:
   - Stop (not terminate) instances between uses
   - Use reserved IP addresses to maintain configuration
   - Storage costs separate (~$0.10/GB/month for stopped instance volumes)

#### On-Demand Per-Request Architecture

**Start instances only when users request GPX generation** - Pay per-minute/per-second:

**How it works**:
1. User makes GPX generation request via API
2. Lambda/Cloud Function starts stopped EC2 instance
3. Request queued or user waits for instance to boot
4. Instance processes route generation
5. Instance auto-stops after job completes

**Typical Flow**:
```
User Request → API Gateway → Lambda (start EC2) 
  → Wait 40-90s for boot → Process job → Auto-stop EC2
```

**Cost Analysis**:
- **Per-request cost**: ~$0.38/hour ÷ 60 = ~$0.006/minute
- **Startup overhead**: 40-90 seconds (standard), 5-10s (optimized)
- **Job duration**: Varies (e.g., 5-30 minutes for route generation)
- **Example**: 10-minute job = 10 × $0.006 = **~$0.06 per request**

**With startup overhead**:
- Standard (60s boot + 10min job): 11 minutes = **~$0.07 per request**
- Optimized (10s boot + 10min job): 10.17 minutes = **~$0.06 per request**

**Monthly costs (assuming 10-minute jobs)**:
- 10 requests/month: **$0.70**
- 50 requests/month: **$3.50**
- 100 requests/month: **$7.00**

**Pros**:
- Ultra-low cost - pay only for actual usage
- Perfect for sporadic, unpredictable usage patterns
- No cost when idle (except minimal storage)
- Scales automatically with demand

**Cons**:
- User wait time: 40-90 seconds for instance to boot (can be optimized to 5-10s)
- Additional complexity: requires Lambda, API Gateway, queue setup
- Cold start penalty on every request
- Not suitable for real-time/instant responses

**Implementation Options**:

1. **AWS Architecture**:
   - API Gateway + Lambda (start EC2) + SQS (queue) + EC2 (process) + Lambda (stop EC2)
   - Lambda IAM role needs `ec2:StartInstances`, `ec2:StopInstances`, `ec2:DescribeInstances`
   - Use CloudWatch to trigger auto-stop after idle time

2. **Google Cloud Architecture**:
   - Cloud Functions + Cloud Scheduler + Compute Engine
   - Similar pattern with GCP-specific services

3. **Azure Architecture**:
   - Azure Functions + Logic Apps + VM
   - Azure Automation for VM lifecycle management

**Optimizations**:
- **Reduce boot time**:
  - Custom minimal AMI with pre-installed dependencies
  - Small root EBS volume
  - Optimized init scripts
  - Can achieve 5-10s boot time (vs. 40-90s default)
  
- **Alternative: Keep instance running**:
  - If requests come within 1-2 hours of each other
  - Set auto-stop timer (e.g., stop after 30 minutes idle)
  - Reduces cost while improving response time

- **Hybrid approach**:
  - Use Render.com free tier for light requests
  - Trigger high-memory EC2 only for complex routes
  - Queue system to handle both paths

**Best for**:
- Unpredictable usage patterns
- Cost-sensitive applications
- Non-time-critical route generation
- Development/testing environments

**Not recommended if**:
- Need instant responses (<1 minute)
- High request volume (>100/day) - better to keep instance running
- Users expect real-time processing

### 6.5 Self-Hosting

For complete control:
- Local server or workstation
- Raspberry Pi cluster (limited performance)
- Used/refurbished hardware

**Trade-off**: Upfront hardware cost, electricity, maintenance.

---

## 7. Recommendations for Jadlo Project

### 7.1 Current Free Hosting (Best Option)

**Render.com Free Tier** (already configured):
- Sufficient for small-to-medium routes
- Uses segmented routing for memory efficiency
- Easy deployment with `render.yaml`
- No credit card required

**Recommendation**: Continue with current Render.com setup for demonstration and light usage.

### 7.2 For Occasional Usage (2-10 Times per Month)

**Best option for intermittent workloads** - Pay only when you use resources:

1. **On-demand instances** (recommended for critical jobs):
   - AWS/GCP/Azure: ~$0.38/hour for 32GB RAM
   - **Cost**: $6-$31/month for 2-10 uses (8 hours each)
   - No interruptions, pay-per-second billing
   - Start instance → Run job → Stop instance

2. **Spot instances** (for cost optimization):
   - AWS/GCP/Azure: ~$0.10/hour (60-90% discount)
   - **Cost**: $1.60-$8/month for 2-10 uses
   - Can be interrupted - best for fault-tolerant jobs
   - Requires interruption handling automation

**Example workflow**:
- Use AWS CLI/SDK to start an m6i.2xlarge instance
- Run your route generation job
- Automatically stop instance when complete
- Total cost: ~$3 for one 8-hour session

See [Section 6.4](#64-occasional-use-2-10-times-per-month) for detailed pricing and automation tips.

### 7.2.1 Per-Request On-Demand (Ultra-Low Cost)

**Start instances only when users request GPX generation**:

**Architecture**: API Gateway → Lambda (start EC2) → Process → Auto-stop

**Cost per request**:
- 10-minute route generation: **~$0.06-$0.07** (including boot time)
- 100 requests/month: **~$7/month**
- Pay per-second billing

**Pros**:
- Ultra-low cost for unpredictable/sporadic usage
- No cost when idle
- Perfect for development or low-traffic applications

**Cons**:
- 40-90 second wait time for boot (can be optimized to 5-10s)
- Additional setup complexity (Lambda, API Gateway, queues)
- Not suitable for real-time responses

**Best for**: Unpredictable usage, cost-sensitive apps, or when users can wait 1-2 minutes.

See subsection "On-Demand Per-Request Architecture" in [Section 6.4](#64-occasional-use-2-10-times-per-month) for implementation details.

### 7.3 For Continuous/Heavy Usage

If 32GB RAM is required 24/7 or very frequently:

1. **Apply for academic/research credits** if affiliated with an institution
2. **Use trial credits** for temporary high-resource needs
3. **Consider reserved instances** (significant savings for continuous use):
   - AWS EC2 m5.2xlarge (32GB): ~$280/month on-demand, ~$170/month reserved
   - GCP n2-highmem-4 (32GB): ~$250/month on-demand, ~$150/month committed
   - Oracle Cloud ARM (24GB): ~$22/month (best value)

### 7.4 Optimization First

Before pursuing high-memory hosting:

1. **Profile memory usage**: Identify actual memory requirements
2. **Optimize algorithms**: Use intersection-based routing
3. **Implement caching**: Reduce redundant OSM queries
4. **Consider dedicated routing engines**: 
   - GraphHopper
   - OSRM
   - Valhalla
   - OpenRouteService

These are optimized for production and use less memory than OSMnx.

---

## 8. Conclusion

**Key Finding**: No cloud provider offers 32GB RAM for free on an always-free basis.

**Best Available Options**:
1. **Oracle Cloud**: 24GB ARM (closest to requirement)
2. **Academic credits**: $5,000-$10,000 for research projects
3. **Per-request on-demand**: ~$0.06-$0.07 per request, ~$7/100 requests
4. **Occasional use on-demand**: $6-$31/month for 2-10 uses
5. **Occasional use spot**: $1.60-$10/month for 2-10 uses
6. **Trial credits**: Temporary access to high-memory instances
7. **Paid tiers**: Required for sustained 24/7 workloads

**For Jadlo Project**:
- Current Render.com setup is appropriate for demonstration
- Memory optimization strategies are already in place
- **For unpredictable/sporadic usage**:
  - Per-request on-demand: ~$0.06/request (user waits 40-90s for boot)
  - Ultra-low cost for occasional use
- **For occasional heavy processing** (2-10 times/month):
  - On-demand instances: $6-$31/month (reliable)
  - Spot instances: $1.60-$10/month (cost-optimized)
- If production-scale 24/7 hosting is needed, consider:
  - Academic cloud credits (if eligible)
  - Reserved instances (significant discount for continuous use)
  - Dedicated routing engines (more efficient than OSMnx)

---

## 9. Additional Resources

### Cloud Free Tier Comparisons
- [Cloud Free Tier Comparison (GitHub)](https://github.com/cloudcommunity/Cloud-Free-Tier-Comparison)
- [Best Always-Free Cloud Platforms](https://github.com/hashirahmad/Best-always-free-tier-cloud-platforms)

### Academic Programs
- [Stanford HAI Google Cloud Grants](https://hai.stanford.edu/research/grant-programs/google-cloud-credit-grants)
- [MIT Cloud Credits Program](https://orcd.mit.edu/resources/major-cloud-provider-credits-program)
- [UW eScience AWS Credits](https://escience.washington.edu/software-engineering/cloud/aws-credits/)

### Alternative Routing Engines
- [GraphHopper](https://www.graphhopper.com/)
- [OSRM](https://project-osrm.org/)
- [Valhalla](https://valhalla.readthedocs.io/)
- [OpenRouteService](https://openrouteservice.org/)

---

**Research Date**: November 2025
