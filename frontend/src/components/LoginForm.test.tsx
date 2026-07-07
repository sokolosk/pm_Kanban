import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { LoginForm } from "@/components/LoginForm";

describe("LoginForm", () => {
  it("renders login form", () => {
    render(<LoginForm onLogin={() => {}} />);
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("calls onLogin with correct credentials", async () => {
    const handleLogin = vi.fn();
    render(<LoginForm onLogin={handleLogin} />);
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole("button", { name: /login/i });
    
    await userEvent.type(usernameInput, "user");
    await userEvent.type(passwordInput, "password");
    await userEvent.click(submitButton);

    expect(handleLogin).toHaveBeenCalledWith("user", "password");
  });

  it("shows validation error when fields empty", async () => {
    const handleLogin = vi.fn();
    render(<LoginForm onLogin={handleLogin} />);

    const submitButton = screen.getByRole("button", { name: /login/i });
    await userEvent.click(submitButton);

    const errorMessage = await screen.findByText(/please enter both/i);
    expect(errorMessage).toBeInTheDocument();
    expect(handleLogin).not.toHaveBeenCalled();
  });

  it("renders backend error message", () => {
    render(<LoginForm onLogin={vi.fn()} error="Invalid credentials" />);
    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
  });
});