import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { vi } from "vitest";
import * as api from "@/lib/api";
import { initialData } from "@/lib/kanban";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

const cloneBoard = () => ({
  id: "board-1",
  title: "Kanban",
  columns: initialData.columns.map((column) => ({
    ...column,
    cardIds: [...column.cardIds],
  })),
  cards: Object.fromEntries(
    Object.entries(initialData.cards).map(([id, card]) => [id, { ...card }])
  ),
});

describe("KanbanBoard", () => {
  let currentBoard = cloneBoard();

  beforeEach(() => {
    currentBoard = cloneBoard();
      vi.spyOn(api, "fetchBoards").mockResolvedValue({ boards: [currentBoard] });
    vi.spyOn(api, "saveBoard").mockImplementation(
      async (_token, _boardId, updatedBoard) => {
        currentBoard = {
          ...updatedBoard,
          columns: updatedBoard.columns.map((column) => ({
            ...column,
            cardIds: [...column.cardIds],
          })),
          cards: Object.fromEntries(
            Object.entries(updatedBoard.cards).map(([id, card]) => [id, { ...card }])
          ),
        };
        return currentBoard;
      }
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const mockProps = {
    token: "fake-token",
    user: { id: 1, username: "user" },
    onLogout: vi.fn(),
  };

  it("renders five columns", async () => {
    render(<KanbanBoard {...mockProps} />);
    await waitFor(() =>
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5)
    );
  });

  it("renames a column", async () => {
    render(<KanbanBoard {...mockProps} />);
    await waitFor(() =>
      expect(screen.queryByText(/loading board/i)).not.toBeInTheDocument()
    );
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await waitFor(() => expect(input).toHaveValue("New Name"));
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard {...mockProps} />);
    await waitFor(() =>
      expect(screen.queryByText(/loading board/i)).not.toBeInTheDocument()
    );
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => expect(within(column).getByText("New card")).toBeInTheDocument());

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    await waitFor(() => expect(within(column).queryByText("New card")).not.toBeInTheDocument());
  });
});
