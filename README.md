# BiznTools public availability

Cloud availability monitor for [BiznTools](https://bizntools.com), authorized November 5, 2026.

This is the separate public `talhasyed986/BiznTools-Status` repository. Only public URLs, public response status and this monitoring code belong there. The application repository, customer data, credentials, research and operating records stay private.

The workflow runs on standard GitHub-hosted Linux runners once an hour at minute 17, with a five-minute limit, bounded requests, HTTPS verification and one retry. It checks four page bodies, the www canonical redirect, sitemap, and a current JavaScript/CSS asset. It stores observations in GitHub, opens one issue for a confirmed probe failure and closes it on recovery. GitHub notification delivery depends on the owner's notification settings. It cannot deploy, change DNS or access Vercel. Its token is limited to this repository's contents and issues.

GitHub scheduled workflows may be delayed or dropped under load. This is independent of the Mac but not an uptime SLA or a zero-downtime guarantee. Each observation commits genuine status evidence; monitor scheduler freshness as well as the healthy flag. An old green observation does not establish current availability.

Standard runners are free in public repositories. No private-repository Actions minutes, paid runner, storage service, account signup or trial is used. The existing application CI hold remains unchanged. The founder approved this separate monitor on November 5, 2026; application CI remains disabled.

Sources: [GitHub billing](https://docs.github.com/en/actions/concepts/billing-and-usage), [schedule limitations](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
