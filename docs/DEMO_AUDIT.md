# Public demo access

Checked November 12, 2026 (Asia/Dhaka).

The [public PeyajFlow demo](https://peyajflow.boraq.io/) returned HTTP 200 when opened outside the restricted network. Its homepage presents a Bangla-first flow picker with English explanations and smartphone and basic-phone SMS modes. The smartphone picker lists six flows, including sign-in and role selection, farmer pricing and sale decisions, trader fulfillment, and buyer demand and order tracking.

Opening the complete smartphone walkthrough on desktop and mobile kept the URL at `/` and displayed the first of 16 screens, a phone-number and OTP example with previous, home, and next controls. The picker fit the tested 1440 × 900 and 360 × 800 viewports without horizontal overflow.

- [Desktop flow picker](design-reviews/demo-desktop.jpg)
- [Mobile flow picker](design-reviews/demo-mobile.jpg)

The role-based paths, bilingual prompts, and compact phone UI are useful interaction references. The walkthrough includes a predetermined sale and profit outcome. Future product screens need dated, sourced market observations and explicit labeling for simulations. Persistence, delivery of OTP or SMS, and trade execution were outside this public walkthrough audit.
