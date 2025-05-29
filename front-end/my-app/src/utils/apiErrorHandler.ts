// utils/apiErrorHandler.ts
export const parseErrorFromResponse = async (response: Response): Promise<Error> => {
    try {
      const data = await response.json();
      if (data?.error?.message) {
        return new Error(`[${data.error.type}] ${data.error.message}`);
      }
      return new Error(`Unknown error from server`);
    } catch {
      return new Error(`Failed to parse error response (Status: ${response.status})`);
    }
  };
  