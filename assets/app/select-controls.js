/* Keep native select values/events as the app's source of truth. */
(() => {
  const controls = new Map();
  let opened = null;
  let sequence = 0;

  function close(restore = false) {
    if (!opened) return;
    const control = opened;
    opened = null;
    control.menu.remove();
    control.button.setAttribute('aria-expanded', 'false');
    if (restore && control.button.isConnected) control.button.focus();
  }

  function position(control) {
    const rect = control.button.getBoundingClientRect();
    const width = Math.min(Math.max(rect.width, 220), innerWidth - 24);
    const below = innerHeight - rect.bottom - 16;
    const above = rect.top - 16;
    const up = below < 180 && above > below;
    const height = Math.max(100, Math.min(340, up ? above : below));
    Object.assign(control.menu.style, {
      width: `${width}px`, left: `${Math.max(12, Math.min(rect.left, innerWidth - width - 12))}px`,
      maxHeight: `${height}px`, top: up ? 'auto' : `${rect.bottom + 8}px`,
      bottom: up ? `${innerHeight - rect.top + 8}px` : 'auto'
    });
  }

  function signature(select) {
    return JSON.stringify(Array.from(select.options, option => [option.textContent, option.selected, option.disabled, option.hidden, option.parentElement.disabled]));
  }

  function options(control, query = '') {
    const focusedIndex = control.list.contains(document.activeElement) ? document.activeElement.dataset.optionIndex : null;
    control.signature = signature(control.select);
    control.list.replaceChildren();
    const needle = query.trim().toLocaleLowerCase();
    let group = null;
    for (const option of control.select.options) {
      if (option.hidden || (needle && !option.textContent.toLocaleLowerCase().includes(needle))) continue;
      const parent = option.parentElement;
      if (parent.tagName === 'OPTGROUP' && parent !== group) {
        const heading = document.createElement('div');
        heading.className = 'app-select-group';
        heading.textContent = parent.label;
        control.list.append(heading);
        group = parent;
      }
      const row = document.createElement('button');
      row.type = 'button';
      row.dataset.optionIndex = String(option.index);
      row.className = 'app-select-option';
      row.setAttribute('role', 'option');
      row.setAttribute('aria-selected', String(option.selected));
      row.tabIndex = -1;
      row.disabled = option.disabled || (parent.tagName === 'OPTGROUP' && parent.disabled);
      const text = document.createElement('span');
      text.textContent = option.textContent;
      const mark = document.createElement('span');
      mark.className = 'app-select-check';
      mark.setAttribute('aria-hidden', 'true');
      mark.textContent = option.selected ? '✓' : '';
      row.append(text, mark);
      row.addEventListener('click', () => {
        if (row.disabled) return;
        const changed = control.select.selectedIndex !== option.index;
        control.select.selectedIndex = option.index;
        close(true);
        sync(control);
        if (changed) {
          control.select.dispatchEvent(new Event('input', { bubbles: true }));
          control.select.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
      control.list.append(row);
    }
    if (focusedIndex != null) {
      const matching = Array.from(control.list.querySelectorAll('[role="option"]:not(:disabled)')).find(row => row.dataset.optionIndex === focusedIndex);
      (matching || control.menu.querySelector('input') || control.list.querySelector('[role="option"]:not(:disabled)') || control.button).focus();
    }
    if (!control.list.querySelector('[role="option"]')) {
      const empty = document.createElement('p');
      empty.className = 'app-select-empty';
      empty.textContent = 'No matching options';
      control.list.append(empty);
    }
  }

  function open(control, query = '') {
    close();
    sync(control);
    if (control.button.disabled) return;
    opened = control;
    control.button.setAttribute('aria-expanded', 'true');
    control.menu.replaceChildren();
    if (control.select.options.length > 10) {
      const search = document.createElement('input');
      search.type = 'search';
      search.placeholder = 'Search options…';
      search.setAttribute('aria-label', `Search ${control.label}`);
      search.value = query;
      search.addEventListener('input', () => options(control, search.value));
      control.menu.append(search);
    }
    control.menu.append(control.list);
    options(control, query);
    document.body.append(control.menu);
    position(control);
    const target = control.menu.querySelector('input') ||
      control.list.querySelector('[aria-selected="true"]:not(:disabled)') ||
      control.list.querySelector('[role="option"]:not(:disabled)');
    target?.focus();
    target?.scrollIntoView({ block: 'nearest' });
  }

  function sync(control) {
    const { select, button, text } = control;
    text.textContent = select.selectedOptions[0]?.textContent || 'Choose an option';
    button.disabled = select.disabled || !select.options.length;
    button.setAttribute('aria-label', `${control.label}: ${text.textContent}`);
    if (opened === control) {
      if (button.disabled || !select.isConnected) close();
      else if (control.signature !== signature(select)) options(control, control.menu.querySelector('input')?.value || '');
    }
  }

  function enhance(select) {
    if (controls.has(select) || select.multiple || select.size > 1) return;
    const label = select.getAttribute('aria-label') || select.labels?.[0]?.querySelector('span')?.textContent || 'Selection';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'app-select';
    button.setAttribute('aria-haspopup', 'listbox');
    button.setAttribute('aria-expanded', 'false');
    const text = document.createElement('span');
    const chevron = document.createElement('span');
    chevron.className = 'app-select-chevron';
    chevron.setAttribute('aria-hidden', 'true');
    chevron.textContent = '⌄';
    button.append(text, chevron);
    const menu = document.createElement('div');
    menu.className = 'app-select-menu';
    const list = document.createElement('div');
    list.id = `app-select-list-${++sequence}`;
    list.setAttribute('role', 'listbox');
    list.setAttribute('aria-label', label);
    button.setAttribute('aria-controls', list.id);
    const control = { select, label, button, text, menu, list };
    controls.set(select, control);
    select.hidden = true;
    select.after(button);
    button.addEventListener('click', () => opened === control ? close(true) : open(control));
    button.addEventListener('keydown', event => {
      if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
        event.preventDefault();
        open(control);
        if (event.key === 'Home' || event.key === 'End') {
          const rows = control.list.querySelectorAll('[role="option"]:not(:disabled)');
          const target = event.key === 'Home' ? rows[0] : rows[rows.length - 1];
          target?.focus();
          target?.scrollIntoView({ block: 'nearest' });
        }
      }
    });
    menu.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); close(true); return; }
      if (event.key === 'Tab') { close(); button.focus(); return; }
      const rows = Array.from(list.querySelectorAll('[role="option"]:not(:disabled)'));
      if (!rows.length) return;
      const index = rows.indexOf(document.activeElement);
      let next;
      if (event.key === 'ArrowDown') next = rows[(index + 1) % rows.length];
      if (event.key === 'ArrowUp') next = rows[index < 1 ? rows.length - 1 : index - 1];
      if (event.key === 'Home' && document.activeElement.tagName !== 'INPUT') next = rows[0];
      if (event.key === 'End' && document.activeElement.tagName !== 'INPUT') next = rows.at(-1);
      if (next) { event.preventDefault(); next.focus(); next.scrollIntoView({ block: 'nearest' }); }
    });
    select.addEventListener('change', () => sync(control));
    control.observer = new MutationObserver(() => sync(control));
    control.observer.observe(select, { childList: true, subtree: true, attributes: true, characterData: true });
    sync(control);
  }

  window.refreshSelectControls = () => { for (const control of controls.values()) sync(control); };
  document.querySelectorAll('select').forEach(enhance);
  new MutationObserver(records => {
    for (const record of records) for (const node of record.addedNodes) {
      if (node.nodeType !== 1) continue;
      if (node.matches('select')) enhance(node);
      node.querySelectorAll('select').forEach(enhance);
    }
    for (const [select, control] of controls) if (!select.isConnected) {
      if (opened === control) close();
      control.observer.disconnect();
      controls.delete(select);
    }
  }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('pointerdown', event => {
    if (opened && !opened.menu.contains(event.target) && !opened.button.contains(event.target)) close();
  });
  document.addEventListener('scroll', event => {
    if (opened && !opened.menu.contains(event.target)) close();
  }, true);
  window.addEventListener('resize', () => close());
  window.addEventListener('blur', () => close());
})();
