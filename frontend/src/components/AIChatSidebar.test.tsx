import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import * as api from "@/lib/api";
import { initialData } from "@/lib/kanban";

describe("AIChatSidebar", () => {
  it("sends a prompt and shows assistant reply", async () => {
    const mockOnBoardUpdate = vi.fn();
    const mockResponse = {
      reply: "Sure, here is the summary",
      board: null,
      board_updated: false,
    };
    vi.spyOn(api, "aiChat").mockResolvedValue(mockResponse);

    render(
      <AIChatSidebar
        token="token"
        board={{ ...initialData, id: "board-1" }}
        onBoardUpdate={mockOnBoardUpdate}
      />
    );

    const textarea = screen.getByPlaceholderText(/ask how to rewrite/i);
    await userEvent.type(textarea, "Summarize the board");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(api.aiChat).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/summary/i)).toBeInTheDocument();
    expect(mockOnBoardUpdate).not.toHaveBeenCalled();
  });
});
