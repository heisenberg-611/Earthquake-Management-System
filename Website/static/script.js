document.addEventListener("DOMContentLoaded", () => {
    const getCellValue = (tr, idx) => {
        let val = tr.children[idx].innerText || tr.children[idx].textContent;
        if (val.startsWith('#')) val = val.substring(1);
        return val;
    };

    const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
        v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
        )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

    document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', (() => {
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        const asc = !th.classList.contains('asc');
        
        Array.from(tbody.querySelectorAll('tr'))
            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), asc))
            .forEach(tr => tbody.appendChild(tr) );
            
        table.querySelectorAll('th').forEach(t => t.classList.remove('asc', 'desc'));
        th.classList.add(asc ? 'asc' : 'desc');
    })));

    // Filtering logic
    const filterTable = (tableId, filters) => {
        const table = document.getElementById(tableId);
        if (!table) return;
        const tbody = table.querySelector('tbody');
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach(tr => {
            // Ignore "No data found" row
            if (tr.children.length <= 1) return;
            
            let showRow = true;
            for (const { colIndex, inputId, isDropdown } of filters) {
                const inputElement = document.getElementById(inputId);
                if (!inputElement) continue;
                const filterVal = inputElement.value.toLowerCase().trim();
                const cellText = (tr.children[colIndex].innerText || tr.children[colIndex].textContent).toLowerCase().trim();
                
                if (filterVal) {
                    if (isDropdown) {
                        if (cellText !== filterVal) showRow = false;
                    } else {
                        if (!cellText.includes(filterVal)) showRow = false;
                    }
                }
            }
            tr.style.display = showRow ? '' : 'none';
        });
    };

    const volName = document.getElementById('filter-name');
    const volEmail = document.getElementById('filter-email');
    const volSkills = document.getElementById('filter-skills');
    const volStatus = document.getElementById('filter-status');
    if (volSkills || volStatus || volName || volEmail) {
        const volFilters = [
            { colIndex: 1, inputId: 'filter-name', isDropdown: false },
            { colIndex: 2, inputId: 'filter-email', isDropdown: false },
            { colIndex: 3, inputId: 'filter-skills', isDropdown: false },
            { colIndex: 4, inputId: 'filter-status', isDropdown: true }
        ];
        if (volName) volName.addEventListener('input', () => filterTable('volunteers-table', volFilters));
        if (volEmail) volEmail.addEventListener('input', () => filterTable('volunteers-table', volFilters));
        if (volSkills) volSkills.addEventListener('input', () => filterTable('volunteers-table', volFilters));
        if (volStatus) volStatus.addEventListener('change', () => filterTable('volunteers-table', volFilters));
    }

    const routePath = document.getElementById('filter-route-path');
    const routeType = document.getElementById('filter-road-type');
    const routeStatus = document.getElementById('filter-route-status');
    if (routePath || routeType || routeStatus) {
        const routeFilters = [
            { colIndex: 0, inputId: 'filter-route-path', isDropdown: false },
            { colIndex: 2, inputId: 'filter-road-type', isDropdown: true },
            { colIndex: 3, inputId: 'filter-route-status', isDropdown: true }
        ];
        if (routePath) routePath.addEventListener('input', () => filterTable('routes-table', routeFilters));
        if (routeType) routeType.addEventListener('change', () => filterTable('routes-table', routeFilters));
        if (routeStatus) routeStatus.addEventListener('change', () => filterTable('routes-table', routeFilters));
    }
});
