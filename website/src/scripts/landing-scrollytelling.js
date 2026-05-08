/* ─── Theme toggle ─── */
(function () {
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var current = document.documentElement.getAttribute('data-theme');
    var next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('starlight-theme', next); } catch (e) {}
  });
})();

/* ─── Scrollytelling: IntersectionObserver ─── */
(function () {
  var isMobile = window.innerWidth <= 960;
  var steps    = document.querySelectorAll('.scroll-step[data-step]');
  var topSent = document.querySelector('.top-sentinel');
  var activeStep = null;

  var nodes = {
    rekor:     document.getElementById('node-rekor'),
    publisher: document.getElementById('node-publisher'),
    registry:  document.getElementById('node-registry'),
    consumer:  document.getElementById('node-consumer'),
  };
  var lines = {
    anchor:       document.getElementById('line-anchor'),
    push:         document.getElementById('line-push'),
    fetch:        document.getElementById('line-fetch'),
    verify:       document.getElementById('line-verify'),
    'rekor-attest': document.getElementById('line-rekor-attest'),
  };
  var labels = {
    anchor:       document.getElementById('lbl-anchor'),
    push:         document.getElementById('lbl-push'),
    fetch:        document.getElementById('lbl-fetch'),
    verify:       document.getElementById('lbl-verify'),
    'rekor-attest': document.getElementById('lbl-rekor-attest'),
  };
  var badges = {
    signed:   document.getElementById('badge-signed'),
    attested: document.getElementById('badge-attested'),
    verified: document.getElementById('badge-verified'),
  };

  function activate(el) { if (el) el.classList.add('active'); }
  function deactivate(el) { if (el) el.classList.remove('active'); }
  function showLabel(lbl) { if (lbl) lbl.setAttribute('opacity', '1'); }
  function hideLabel(lbl) { if (lbl) lbl.setAttribute('opacity', '0'); }

  var lineMarkers = {
    anchor:         'url(#m12-signed)',
    push:           'url(#m12-attested)',
    fetch:          'url(#m12-verified)',
    verify:         'url(#m12-verified)',
    'rekor-attest': 'url(#m12-attested)',
  };
  function activateLine(key) {
    var el = lines[key];
    if (!el) return;
    el.classList.add('active');
    el.setAttribute('marker-end', lineMarkers[key]);
  }
  function deactivateLine(key) {
    var el = lines[key];
    if (!el) return;
    el.classList.remove('active');
    el.removeAttribute('marker-end');
  }

  function resetAll() {
    Object.values(nodes).forEach(deactivate);
    Object.keys(lines).forEach(deactivateLine);
    Object.values(badges).forEach(deactivate);
    Object.values(labels).forEach(hideLabel);
  }

  function setStep(step) {
    if (step === activeStep) return;
    activeStep = step;

    steps.forEach(function (el) {
      el.classList.toggle('active', el.dataset.step === step);
    });

    resetAll();
    activate(nodes.rekor);

    /* Step 01: publisher signs and logs to Rekor */
    if (step === 'signed' || step === 'published' || step === 'attested' || step === 'verified') {
      activate(nodes.publisher);
      activateLine('anchor');
      showLabel(labels.anchor);
      activate(badges.signed);
    }

    /* Step 02: publisher pushes manifest to registry */
    if (step === 'published' || step === 'attested' || step === 'verified') {
      activate(nodes.registry);
      activateLine('push');
      showLabel(labels.push);
    }

    /* Step 03: registry attests and logs to Rekor */
    if (step === 'attested' || step === 'verified') {
      activateLine('rekor-attest');
      showLabel(labels['rekor-attest']);
      activate(badges.attested);
    }

    /* Step 04: consumer fetches index and verifies against Rekor */
    if (step === 'verified') {
      activate(nodes.consumer);
      activateLine('fetch');
      activateLine('verify');
      showLabel(labels.fetch);
      showLabel(labels.verify);
      activate(badges.verified);
    }
  }

  var stepObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) setStep(e.target.dataset.step);
    });
  }, { rootMargin: isMobile ? '-20% 0% -20% 0%' : '-38% 0% -38% 0%', threshold: 0 });

  steps.forEach(function (s) { stepObserver.observe(s); });

  if (topSent) {
    var topObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) setStep('intro');
      });
    }, { rootMargin: '0% 0% -30% 0%', threshold: 0 });
    topObserver.observe(topSent);
  }

  setStep('intro');
})();
