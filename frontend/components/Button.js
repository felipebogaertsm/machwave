export default function Button(props) {
    return (
        <button
            className='
                px-6 py-2 bg-slate-200 font-semibold uppercase 
                tracking-wider rounded-full whitespace-nowrap
                border-2 border-transparent
                hover:border-slate-700
                hover:bg-slate-900 hover:text-slate-200
                transition-all duration-200
            '
            {...props}
        >
            {props.children}
        </button>
    )
}
