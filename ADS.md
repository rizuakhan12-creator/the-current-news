# Advertising setup

All four placements use the same reusable `ad(slot)` generator and `data-ad-slot` browser loader: `homepage`, `article` (after paragraph two), `sidebar`, and `footer`. They are labeled and reserve space. No popup, push prompt, auto redirect or sticky overlay advertising is installed. Policy/contact pages contain no in-body ad placements.

## Google AdSense

1. Apply with your actual domain and substantive original content. Complete site ownership verification using the exact method in your publisher dashboard. For a verification meta tag, add the supplied tag to a trusted head file referenced by `cmp_head_file` only after adapting the build if verification must load while ads are disabled; alternatively use the dashboard's ads.txt verification method.
2. In `config/ads.json`, choose `network: "adsense"`; paste your real public `ca-pub-...` client in `adsense_client`, then put each actual ad-unit number in the corresponding `slots` value. These public IDs are not API secrets. No fictional IDs are provided.
3. Set up consent as below. Enable `enabled: true` only after the site is approved and consent is connected. The production build is also required. The loader requests the official AdSense library once and creates the configured display units. Keep Auto ads disabled if you want only these four placements.
4. Use the publisher dashboard's testing guidance, then verify placement rendering and policy-center status on the approved domain. Never click your own ads.

## Adsterra and Monetag

Choose `network: "adsterra"` or `"monetag"`. Paste **real, vendor-issued, non-intrusive display/native HTML code** as JSON strings into `custom_snippets.homepage`, `.article`, `.sidebar` and `.footer`; leave unused slots empty. Use a JSON editor so quotes and newlines are escaped correctly. Never paste API keys or publisher account access tokens.

Custom tags run in sandboxed iframe documents (`allow-scripts allow-popups`) after consent. They cannot navigate the top page or access its DOM. Some network tags require first-party origin access, top-level execution or service workers and will not work inside this integration. Do not remove the sandbox reflexively. Ask the network for a compatible display format; leave an unsupported slot disabled. In particular, Monetag’s available website formats do not necessarily include a conventional four-slot display banner. This prepares a configurable adapter, not a guarantee that every account’s tag works in a frame. Push, popunder, interstitial and service-worker tags are outside this integration.

Follow the actual dashboard instructions for domain verification and permitted formats. See [Adsterra native banners](https://adsterra.com/blog/turn-a-profit-with-native-banners/) and [Monetag website verification](https://help.monetag.com/en/articles/6726312-how-do-i-get-started-as-a-publisher-add-and-verify-your-website-s). Keep the exact vendor consent and tagging requirements intact; a sandbox does not itself make an ad compliant.

## Consent integration

The built-in privacy panel records a local optional-ad choice. **It is not a certified CMP.** Production ad loads require BOTH the local choice and a publisher-provided CMP signal. Without a CMP adapter, no ads load even if a visitor clicks Allow optional ads. This is deliberately fail-closed.

Configure your consent provider using its official instructions. Put its approved head snippet and your adapter in a trusted `.html` file within the project, for example `config/cmp-head.html`, then set `cmp_head_file` to that path. It is inserted only in production when ads are enabled. Do not put credentials in that file. Your CMP loader must itself respect its provider’s consent and regional behavior requirements.

After the CMP has checked all required purposes, vendors, region rules and consent expiry, the adapter can notify this site:

```js
// Only inside a successful, validated CMP callback, never unconditionally:
window.currentAdConsent = true;
window.dispatchEvent(new CustomEvent('current:ad-consent', {detail: true}));

// When vendor/purpose consent is withdrawn or unavailable:
window.currentAdConsent = false;
window.dispatchEvent(new CustomEvent('current:ad-consent', {detail: false}));
```

If the CMP resolves before the app script loads, the initial global value is read when configuration arrives. The adapter must re-evaluate on each page load and on consent changes. For Google, use the provider's supported TCF / Google consent signal integration as well; this boolean is only the local loading gate and does not replace vendor consent signals. The footer offers local withdrawal and reloads to stop future ad requests. Include a link to the CMP's own preferences UI and cookie/data-rights tools in your production privacy policy.

Google has specific CMP requirements for relevant regions; use a Google-certified CMP where required. Review [Google’s current CMP requirements](https://support.google.com/adsense/answer/13554116?hl=en). Have the responsible publisher adapt privacy disclosures and consent rules to its audience, jurisdiction and chosen vendors before enabling ads.

## ads.txt

Replace the comments in `static/ads.txt` with the exact seller records from each network dashboard. Do not guess a seller ID or certification ID. One record goes on each line. Rebuild; confirm `https://YOUR_DOMAIN/ads.txt` returns plain text without authentication. Confirm authorized-seller status in the dashboard after its crawler refreshes.

For GitHub repository Pages, `/REPOSITORY/ads.txt` is not the domain-root URL. Use a custom domain or maintain the correct domain-root ads.txt in the account's root Pages site as permitted by the network. Do not publish seller entries for accounts you do not control.

## Monetization operations

Publish useful reporting consistently, maintain transparent authorship and corrections, and build a real audience before expecting revenue. Start with few slots; inspect mobile performance, readability, ad quality and consent behavior. Monitor network policy notices, invalid traffic and actual revenue in the publisher dashboard. No particular income or network approval is promised.
