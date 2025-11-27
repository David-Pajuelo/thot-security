import * as React from "react";

type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={`border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none ${className}`}
      {...props}
    />
  );
});

Input.displayName = "Input";

export { Input };
