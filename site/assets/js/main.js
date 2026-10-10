/* ============================================================
   GHOST — Personal Archive · 交互与数据渲染
   ============================================================ */
(function () {
  'use strict';
  var D = window.SITE_DATA;
  if (!D) return;

  /* ---------- 封面图地址（data.js 中已提供 cover 工具） ---------- */
  function coverFor(item) {
    var size = item.aspect === '16-10' ? 'landscape_16_9' : 'landscape_4_3';
    return (typeof cover === 'function' ? cover(item.coverPrompt, size)
      : 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' +
        encodeURIComponent(item.coverPrompt) + '&image_size=' + size);
  }

  /* ---------- 导航链接 ---------- */
  var navLinks = document.getElementById('navLinks');
  navLinks.innerHTML = D.nav.map(function (n) {
    return '<a href="' + n.href + '">' + n.label + '</a>';
  }).join('');

  /* ---------- 精选作品 ---------- */
  var worksGrid = document.getElementById('worksGrid');
  worksGrid.innerHTML = D.works.map(function (w) {
    var cls = 'work reveal';
    if (w.reverse) cls += ' work--reverse';
    if (w.offset) cls += ' work--offset';
    var tags = '<li class="tag--placeholder">占位</li>' +
      w.tags.map(function (t) { return '<li>' + t + '</li>'; }).join('');
    return '<article class="' + cls + '">' +
      '<a class="work__media ar-' + w.aspect + '" href="#" title="占位链接">' +
        '<img src="' + coverFor(w) + '" alt="占位封面：' + w.title + '" loading="lazy" />' +
      '</a>' +
      '<div class="work__body">' +
        '<p class="work__meta"><span class="work__cat">' + w.category + '</span> · ' + w.date + '</p>' +
        '<h3 class="work__title"><a href="#" title="占位链接">' + w.title + '</a></h3>' +
        '<p class="work__summary">' + w.summary + '</p>' +
        '<ul class="work__tags">' + tags + '</ul>' +
      '</div>' +
    '</article>';
  }).join('');

  /* ---------- 最近随笔 ---------- */
  var notesList = document.getElementById('notesList');
  notesList.innerHTML = D.notes.map(function (n) {
    return '<li class="note reveal">' +
      '<div class="note__meta">' +
        '<span class="note__date">' + n.date + '</span>' +
        '<span class="note__cat">' + n.category + '</span>' +
      '</div>' +
      '<h3 class="note__title"><a href="#" title="占位链接">' + n.title + '</a></h3>' +
      '<p class="note__sum">' + n.summary + '</p>' +
    '</li>';
  }).join('');

  /* ---------- About ---------- */
  document.querySelector('.about__lead').textContent = D.about.lead;
  document.querySelector('.about__paras').innerHTML =
    D.about.paragraphs.map(function (p) { return '<p>' + p + '</p>'; }).join('');
  document.querySelector('.about__interests').innerHTML =
    D.about.interests.map(function (i) { return '<li>' + i + '</li>'; }).join('');

  /* ---------- 页脚 ---------- */
  document.getElementById('footerSocial').innerHTML =
    D.social.map(function (s) {
      return '<a href="' + s.href + '" title="占位链接，待替换为真实公开链接">' + s.label + '</a>';
    }).join('');
  document.getElementById('footerClosing').textContent = D.footer.closing;
  document.getElementById('footerNote').textContent = D.footer.note;
  document.getElementById('year').textContent = new Date().getFullYear();

  /* ---------- 导航滚动状态 ---------- */
  var nav = document.getElementById('nav');
  function onScroll() {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- 移动端菜单 ---------- */
  var toggle = document.getElementById('navToggle');
  toggle.addEventListener('click', function () {
    var open = navLinks.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.textContent = open ? '关闭' : '菜单';
  });
  navLinks.addEventListener('click', function (e) {
    if (e.target.tagName === 'A' && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = '菜单';
    }
  });

  /* ---------- Hero 元素错峰 ---------- */
  var heroReveals = document.querySelectorAll('.hero .reveal');
  Array.prototype.forEach.call(heroReveals, function (el, i) {
    el.style.transitionDelay = (0.08 * i) + 's';
  });

  /* ---------- 滚动淡入 ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('in'); });
  }
})();
