/* No secrets or source excerpts enter this browser bundle. */
(() => {
  'use strict';
  const base = new URL('.', document.currentScript.src);
  const storage = {get(k){try{return localStorage.getItem(k)}catch{return null}},set(k,v){try{localStorage.setItem(k,v)}catch{}}};
  const theme = storage.get('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;
  document.querySelector('#theme')?.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next; storage.set('theme', next);
  });
  document.querySelector('#share')?.addEventListener('click', async () => {
    const status = document.querySelector('#share-status');
    try {await navigator.clipboard.writeText(location.href);status.textContent = 'Link copied.'}
    catch {status.textContent = 'Copy the address from your browser to share.'}
  });
  const consent = document.querySelector('#consent');
  let consentConfig;
  const loaded = new Set();
  function externalApproval() {
    // Only a trusted publisher CMP adapter should call this after checking vendor/purpose consent.
    return window.currentAdConsent === true;
  }
  async function loadAds() {
    const config = consentConfig;
    if (!config?.enabled || storage.get('ad-choice') !== 'allow' || !externalApproval()) return;
    if (config.network === 'adsense' && /^ca-pub-\d{16}$/.test(config.adsense_client)) {
      if (!loaded.has('adsense')) {
        const script = document.createElement('script');
        script.async = true; script.crossOrigin = 'anonymous';
        script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(config.adsense_client);
        document.head.append(script); loaded.add('adsense');
      }
      document.querySelectorAll('[data-ad-slot]').forEach(target => {
        const slot = config.slots[target.dataset.adSlot];
        if (!/^\d+$/.test(slot) || loaded.has(target)) return;
        const ad = document.createElement('ins'); ad.className = 'adsbygoogle';ad.style.display = 'block';
        ad.dataset.adClient = config.adsense_client;ad.dataset.adSlot = slot;ad.dataset.adFormat = 'auto';ad.dataset.fullWidthResponsive = 'true';
        target.append(ad); (window.adsbygoogle = window.adsbygoogle || []).push({});loaded.add(target);
      });
    } else if (['adsterra','monetag'].includes(config.network)) {
      document.querySelectorAll('[data-ad-slot]').forEach(target => {
        const snippet = config.custom_snippets[target.dataset.adSlot];
        if (!snippet || loaded.has(target)) return;
        // Trusted publisher-controlled snippets only. Isolated frame prevents snippets taking over the page.
        const frame = document.createElement('iframe');frame.title = 'Advertisement';
        frame.setAttribute('sandbox','allow-scripts allow-popups');frame.referrerPolicy = 'strict-origin-when-cross-origin';
        frame.style.cssText = 'border:0;width:100%;min-height:250px';frame.srcdoc = snippet;
        target.append(frame);loaded.add(target);
      });
    }
  }
  function choose(choice) {
    storage.set('ad-choice',choice);consent.hidden = true;
    if (choice === 'allow') loadAds(); else location.reload();
  }
  document.querySelector('#privacy-settings')?.addEventListener('click', () => {consent.hidden=false;document.querySelector('#reject').focus()});
  document.querySelector('#reject')?.addEventListener('click', () => choose('deny'));
  document.querySelector('#accept')?.addEventListener('click', () => choose('allow'));
  window.addEventListener('current:ad-consent', event => {
    window.currentAdConsent = event.detail === true;
    if (!window.currentAdConsent) {
      document.querySelectorAll('[data-ad-slot]').forEach(x => x.replaceChildren());
      if (loaded.size) {storage.set('ad-choice','deny'); location.reload()}
    } else loadAds();
  });
  fetch(new URL('ads.json',base)).then(r=>{if(!r.ok)throw Error();return r.json()}).then(config=>{
    consentConfig=config;
    if(config.enabled && !storage.get('ad-choice'))consent.hidden=false;
    loadAds();
  }).catch(()=>{});
  const form = document.querySelector('#search-form');
  if (!form) return;
  const query=document.querySelector('#query'), category=document.querySelector('#category');
  const results=document.querySelector('#results'), count=document.querySelector('#result-count');
  let articles=[];
  query.value = new URLSearchParams(location.search).get('q') || '';
  function render() {
    const words=query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const found=articles.filter(a=>(!category.value || a.category===category.value) && words.every(w=>[a.title,a.summary,...a.tags].join(' ').toLocaleLowerCase().includes(w)));
    results.replaceChildren(); count.textContent = `${found.length} ${found.length===1?'story':'stories'} found`;
    for(const a of found) {
      const card=document.createElement('article');card.className='card';
      const copy=document.createElement('div');copy.className='card-copy';
      const tag=document.createElement('span');tag.className='eyebrow';tag.textContent=a.category;
      const heading=document.createElement('h3'), anchor=document.createElement('a');
      anchor.href=new URL('../articles/'+encodeURIComponent(a.slug)+'/',base);anchor.textContent=a.title;
      heading.append(anchor);const summary=document.createElement('p');summary.textContent=a.summary;
      copy.append(tag,heading,summary);card.append(copy);results.append(card);
    }
    if(!found.length){const p=document.createElement('p');p.textContent='Try a broader keyword or another category.';results.append(p)}
  }
  form.addEventListener('submit',event=>{event.preventDefault();const url=new URL(location.href);url.searchParams.set('q',query.value);history.replaceState(null,'',url);render()});
  category.addEventListener('change',render);query.addEventListener('input',render);
  fetch(new URL('search.json',base)).then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{articles=data;render()}).catch(()=>{count.textContent='Search is unavailable. Browse the category links above.'});
})();
