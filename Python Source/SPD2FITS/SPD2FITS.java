/*

	SPD2FITS is a tool to convert SPD data files produced by SkyPipe (radiosky.com)
	into FITS binary tables.

	SPD2FITS V0.2 06-APR-2005
	(C) 2004-5 by jupiterradio.com
	http://www.jupiterradio.com
	
	SPD file format (C) by radiosky.com
	http://www.radiosky.com
	
	JavaFits (C) by NASA
	http://heasarc.gsfc.nasa.gov/docs/heasarc/fits/java/v0.9/
	
	For updates of SPD2FITS, check: http://www.jupiterradio.com

	Copying, distribution, altering of the SPD2FITS-source:
	Free, as long as this notice remains unchanged!

	Disclaimer: jupiterradio.com cannot be held liable for anything
	
	Supports the following data formats for now:
	[Date] (8 bytes)
	[Channel 1 Data] (8 bytes)
	( [Channel 2 Data] (8 bytes) )
	( [Channel 3 Data] (8 bytes) )

	Integer Save format:
	[Date] (8 bytes)
	[Channel 1 Data] (8 bytes)
	( [Channel 2 Data] (2 bytes) )
	( [Channel 3 Data] (2 bytes) )
	
	Compile with:
	# javac -classpath javafits/fits.jar:javafits/util.jar SPD2FITS.java
	Run with:
	# java -classpath javafits/fits.jar:javafits/util.jar:javafits/image.jar:. SPD2FITS file.spd
	
	TODO: add SPD-MetaData to COMMENTS in the FITS HEADER
*/

import java.io.*;
import nom.tam.util.*;
import nom.tam.fits.*;

public class SPD2FITS {
	public static void main(String[] args) throws Exception {
		String version = "0.1";
		int timebytes = 8;
		int databytes = 8;
		boolean isintsaveformat = false;
		try {
			File file = new File(args[0]);
			InputStream is = new FileInputStream(file);
			DataInputStream dis = new DataInputStream( is );
			long length = file.length();
			if (length > Integer.MAX_VALUE) {
				throw new IOException("File is too large");
			} else {
				byte[] bytes = new byte[(int)length];
				int offset = 0;
				int numRead = 0;
				while (offset < bytes.length && (numRead = is.read(bytes, offset, bytes.length-offset) ) >= 0) {
					offset += numRead;
				}
				if (offset < bytes.length) {
					throw new IOException("Could not completely read file "+file.getName());
				}
				dis.close();
				is.close();
				double start = arr2double(bytes, 10);			
				double finish = arr2double(bytes, 18);			
				double lat = arr2double(bytes, 26);			
				double lng = arr2double(bytes, 34);			
				double maxy = arr2double(bytes, 42);			
				double miny = arr2double(bytes, 50);			
				double timezone = arr2int(bytes, 58);			
				String source = arr2str(bytes, 60, 10);
				String author = arr2str(bytes, 70, 20);
				String localname = arr2str(bytes, 90, 20);
				String location = arr2str(bytes, 110, 40);
				int channels = arr2int(bytes, 150);			
				long notelength = arr2int(bytes, 152);			
				String note = arr2str(bytes, 156, (int)notelength);
				int begindata = 156 + (int)notelength;
				int datalen = 0;
				if (note.indexOf("Integer Save") > 0) {
					databytes = 2;
					isintsaveformat = true;
				}
				if (channels == 1) {
					datalen = (int) ( ( length - (156 + notelength) ) / (timebytes + databytes) );
				} else if (channels == 2) {
					datalen = (int) ( ( length - (156 + notelength) ) / (timebytes + databytes * 2) );
				} else { // 3 channels
					datalen = (int) ( ( length - (156 + notelength) ) / (timebytes + databytes * 3) );
				}
				double[] time  = new double[datalen];
				double[] ch1  = new double[datalen];
				double[] ch2  = new double[datalen];
				double[] ch3  = new double[datalen];
				int cnt = 0;
				for (int i = 0; i < datalen; i++) {
					time[i] = arr2double(bytes, begindata + cnt);
					if (isintsaveformat) {
						ch1[i] = (double)arr2int(bytes, begindata + (cnt + timebytes) );
					} else {
						ch1[i] = arr2double(bytes, begindata + (cnt + timebytes) );
					}
					if (channels == 3) {
						if (isintsaveformat) {
							ch2[i] = (double)arr2int(bytes, begindata + (cnt + timebytes + databytes) );
							ch3[i] = (double)arr2int(bytes, begindata + (cnt + timebytes + databytes*2) );
						} else {
							ch2[i] = arr2double(bytes, begindata + (cnt + timebytes + databytes) );
							ch3[i] = arr2double(bytes, begindata + (cnt + timebytes + databytes*2) );
						}
						cnt = cnt + timebytes + databytes * 3;
					} else if (channels == 2) {
						if (isintsaveformat) {
							ch2[i] = (double)arr2int(bytes, begindata + (cnt + timebytes + databytes) );
						} else {
							ch2[i] = arr2double(bytes, begindata + (cnt + timebytes + databytes) );
						}
						cnt = cnt + timebytes + databytes * 2;
					} else {
						cnt = cnt + timebytes + databytes;
					}
				}
				FitsFactory.setUseAsciiTables(false);
				Fits f = new Fits();
				if (channels == 3) {
					BasicHDU myhdu = Fits.makeHDU(new Object[]{ time, ch1, ch2, ch3});
					f.addHDU(myhdu);
				} else if (channels == 2) {
					BasicHDU myhdu = Fits.makeHDU(new Object[]{ time, ch1, ch2});
					f.addHDU(myhdu);
				} else {
					BasicHDU myhdu = Fits.makeHDU(new Object[]{ time, ch1});
					f.addHDU(myhdu);
				}
				BinaryTableHDU bhdu = (BinaryTableHDU) f.getHDU(1);
				bhdu.setColumnName(0,"TIME", null);
				bhdu.setColumnName(1,"CH1", "Channel 1");
				if (channels == 2) {
					bhdu.setColumnName(2,"CH2", "Channel 2");
				} else if (channels == 3) {
					bhdu.setColumnName(2,"CH2", "Channel 2");
					bhdu.setColumnName(3,"CH3", "Channel 3");
				}
				bhdu.addValue("AUTHOR", author, "Author");
				bhdu.addValue("LOCALNAM", localname, "Localname");
				bhdu.addValue("LOCATION", location, "Location");
				bhdu.addValue("LATITUDE", lat, "Latitude");
				bhdu.addValue("LONGITUD", lng, "Longitude");
				bhdu.addValue("CHANNELS", channels, "Number of channels");
				Header hdr = bhdu.getHeader();
				String[] notearr = note.split("\r\n");
				for (int i = 0; i < notearr.length; i++) {
					if (!notearr[i].startsWith("*")) {
						hdr.insertComment(notearr[i]);
					}				
				}
				hdr.insertComment(" Converted with SPD2FITS V"+version+": www.jupiterradio.com ");
				BufferedFile bf = new BufferedFile(args[0]+".fits", "rw");
				f.write(bf);
				bf.flush();
				bf.close();
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
	}
	
	public static String arr2str(byte[] arr, int start, int len) {
		int i = 0;
		int cnt = 0;
		byte[] tmp = new byte[len];
		for (i = start; i < (start + len); i++) {
			if ( arr[i] <= 0 ){
				tmp[cnt] = 32;  // temporary hack for values < 0 ; otherwise the FITS table is unreadable
			} else {
				tmp[cnt] = arr[i];
			}
			cnt++;
		}
		String ret = new String(tmp);
		return ret;
	}
	
	public static double arr2double (byte[] arr, int start) {
		int i = 0;
		int len = 8;
		int cnt = 0;
		byte[] tmp = new byte[len];
		for (i = start; i < (start + len); i++) {
			tmp[cnt] = arr[i];
			cnt++;
		}
		long accum = 0;
		i = 0;
		for ( int shiftBy = 0; shiftBy < 64; shiftBy += 8 ) {
			accum |= ( (long)( tmp[i] & 0xff ) ) << shiftBy;
			i++;
		}
		return Double.longBitsToDouble(accum);
	}
	
	public static long arr2long (byte[] arr, int start) {
		int i = 0;
		int len = 4;
		int cnt = 0;
		byte[] tmp = new byte[len];
		for (i = start; i < (start + len); i++) {
			tmp[cnt] = arr[i];
			cnt++;
		}
		long accum = 0;
		i = 0;
		for ( int shiftBy = 0; shiftBy < 32; shiftBy += 8 ) {
			accum |= ( (long)( tmp[i] & 0xff ) ) << shiftBy;
			i++;
		}
		return accum;
	}

	public static int arr2int (byte[] arr, int start) {
		int low = arr[start] & 0xff;
		int high = arr[start+1] & 0xff;
		return (int)( high << 8 | low );
	}

}


