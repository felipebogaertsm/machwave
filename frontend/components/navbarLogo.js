// -* - coding: utf - 8 -* -
// Author: Felipe Bogaerts de Mattos
// Contact me at felipe.bogaerts@engenharia.ufjf.br.
// This program is free software: you can redistribute it and / or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.

export default function NavbarLogo(props) {
    return (
        <button
            className='
                px-4 h-full my-auto rounded-md font-bold text-xl
                opacity-70 hover:opacity-100
                transition-all duration-200
            '
            {...props}
        >
            {props.children}
        </button>
    )
}
