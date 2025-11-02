# Research: Free Hosting with 32GB RAM

## Executive Summary

After thorough research of cloud hosting options in 2024, **no major cloud provider offers an always-free tier with 32GB of RAM**. Free tiers are designed for learning, prototyping, and small workloads, typically providing 1-2GB of RAM at most.

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

### 6.4 Self-Hosting

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

### 7.2 For Heavy Usage (If Needed)

If 32GB RAM is genuinely required for production:

1. **Apply for academic/research credits** if affiliated with an institution
2. **Use trial credits** for temporary high-resource needs
3. **Consider paid tiers**: 
   - AWS EC2 m5.2xlarge (32GB): ~$0.38/hour = ~$280/month
   - GCP n2-highmem-4 (32GB): ~$0.34/hour = ~$250/month
   - Oracle Cloud ARM (24GB): ~$0.03/hour = ~$22/month (best value)

### 7.3 Optimization First

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
3. **Trial credits**: Temporary access to high-memory instances
4. **Paid tiers**: Required for sustained 32GB+ workloads

**For Jadlo Project**:
- Current Render.com setup is appropriate for demonstration
- Memory optimization strategies are already in place
- If production-scale hosting is needed, consider:
  - Academic cloud credits (if eligible)
  - Paid cloud instances (most reliable)
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

**Research Date**: November 2024
