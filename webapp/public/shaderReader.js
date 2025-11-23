// Function to read a text file and return its content as a promise
async function readTextFile(file) {
    try {
        const response = await fetch(file);
        if (!response.ok) throw new Error("Network response was not ok");
        const content = await response.text();
        return content;
    } catch (error) {
        console.error("Error fetching file:", error);
    }
    return null;
}

export default readTextFile;