import { useRef, useEffect } from 'react'

export default function FormControl({ title, type = 'text', value = '', placeholder = '', onChange }) {
    var isPasswordShown = false
    const inputElement = useRef();
    const imgElement = useRef();

    function passwordShowHideHandler() {
        if (isPasswordShown) {
            inputElement.current.type = 'password'
            isPasswordShown = false
            imgElement.current.src = `${imgElement.current.src}`.replace('eye', 'eye_slash')
        } else {
            inputElement.current.type = 'text'
            isPasswordShown = true
            imgElement.current.src = `${imgElement.current.src}`.replace('eye_slash', 'eye')
        }
    }

    useEffect(() => {
        inputElement.current.value = value
    }, [])

    return (
        <div
            className="
                flex flex-col space-y-2 w-full
            "
        >
            <label>{title}</label>
            <div className='flex flex-row justify-center space-x-2'>
                <input
                    className='w-full'
                    type={type}
                    placeholder={placeholder}
                    onChange={onChange}
                    ref={inputElement}
                >
                </input>
                {type === 'password' && (
                    <span
                        className='
                                w-14 p-2 bg-zinc-200 rounded-xl border-solid
                                flex justify-center cursor-pointer transition-all 
                                duration-200 group border-2 border-transparent
                                hover:border-slate-500
                            '
                        onClick={passwordShowHideHandler}
                    >
                        <img
                            src={`/icons/eye_slash.svg`}
                            className='
                                    place-self-center w-6 
                                    group-hover:scale-105 transition-all
                                    duration-200 opacity-70 
                                    group-hover:opacity-90
                                '
                            ref={imgElement}
                        ></img>
                    </span>
                )}
            </div>
        </div>
    )
}
