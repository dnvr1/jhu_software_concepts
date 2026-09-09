# Access events

On September 9, 2026, the Edge control connection closed locally after record
2,420. Its tab remained blank in a loading state; no HTTP rejection was reported.

A fresh anonymous Chrome profile then checked robots.txt. Its first automated
survey navigation returned HTTP 403, so collection stopped without retrying.
The user subsequently completed Cloudflare's normal manual verification, as
permitted by the assignment update. Before resume, the same Chrome page showed
the expected public table, an optional Sign In link, no password form, no
authenticated marker, and no account/logout controls. The exact saved cursor
remained unchanged.

One controlled resume is authorized from the saved checkpoint with a slower
10-second delay. This is not a challenge bypass: verification was manual, the
page is public and anonymous, and the prior rejection remains documented. A
new rejection, challenge, login requirement, or access change is a stop condition.

At 10,220 records, the local Chrome DevTools WebSocket ended with Windows error
10054. This was a browser-control transport failure: there was no HTTP denial,
challenge, rate-limit response, or robots-policy change. The saved checkpoint
and all 10,220 unique records remained intact. At the user's explicit direction,
the existing anonymous Chrome profile was reviewed again on September 9, 2026:
the public robots.txt policy was readable and the exact saved next-page cursor
loaded as a GradCafe admissions-results page. A narrowly scoped recovery method
recorded that evidence in checkpoint history and resumed one collector at the
unchanged 10-second delay. It cannot clear access, policy, challenge, HTTP, rate
limit, or unrelated transport stops.

At 15,240 committed records, Windows briefly denied the atomic replacement of
`applicant_data.json`. The complete HTML and JSON for page 763 had already been
archived. Its hash, schema version, source cursor, parsed count, and next cursor
were checked locally before recovery. The save layer now retries only transient
`PermissionError` failures for a bounded interval while retaining the complete
temporary file; other filesystem errors still fail immediately. A separately
guarded recovery recorded the review, reconciled page 763 without another web
request, and produced 15,260 unique records with all 20 archived URLs present.

At 22,280 records, the WebSocket client reported its exact local message,
`Connection to remote host was lost.` Chrome's debugging port remained open,
the last visible result cursor was exactly one page behind the saved next cursor,
and no orphan page 1,115 existed. At the user's explicit direction, the public
robots.txt policy was loaded and read again in the same anonymous profile. The
reviewed transport guard was extended only for this exact client message; HTTP,
challenge, rate-limit, policy, and similar-looking compound errors remain
blocking. Collection was then authorized to resume at the saved cursor with the
unchanged 10-second delay.
