// -* - coding: utf - 8 -* -
// Author: Felipe Bogaerts de Mattos
// Contact me at felipe.bogaerts@engenharia.ufjf.br.
// This program is free software: you can redistribute it and / or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.

export default function NavbarItem({ children }) {
    return (
        <button
            className='
                px-4 bg-slate-500 h-full my-auto bg-opacity-0
                hover:bg-opacity-50 rounded-md font-bold
                transition-all duration-100
            '
        >
            {children}
        </button>
    )
}
