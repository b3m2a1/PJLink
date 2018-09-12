/********************************************************************

   JLinkNativeLibrary.c - source file for the J/Link native library

   J/Link source code (c) 1999-2004, Wolfram Research, Inc. All rights reserved.

   Use is governed by the terms of the J/Link license agreement, which can be
   found at www.wolfram.com/solutions/mathlink/jlink.

   Author: Todd Gayley

*********************************************************************/

/* TODO

	Not yet Unicode savvy for MLCheckFunction, MLCheckFunctionWithArgCount,
	MLGetArray, MLPutArray.

	Have Java-side yield func passed in as argument. This will remove
	all vestiges of a dependence on the properties of the class that
	hosts the native methods.
*/


#define JDEBUGLEVEL 0

#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <signal.h>

#if defined(DARWIN_MATHLINK) || defined(X86_DARWIN_MATHLINK) || defined(X86_64_DARWIN_MATHLINK)
#include <ApplicationServices/ApplicationServices.h>
#endif

#include "mathlink.h"
#include "com_wolfram_jlink_NativeLink.h"

#ifdef WINDOWS_MATHLINK
/* On Windows, need to load jawt.dll to get HWNDs from a Java window.
   Load the DLL dynamically to avoid fatal problems that have occurred in
   non-standard runtime environments where jawt.dll cannot be found.
*/
#include <jawt.h>
#include <jawt_md.h>
HINSTANCE hJawtLib = NULL;
typedef jboolean (JNICALL *GET_AWT_PROC) (JNIEnv* env, JAWT* awt);
GET_AWT_PROC getAWTproc = NULL;
#endif

#define MLFUNC(meth)        JNICALL Java_com_wolfram_jlink_NativeLink_##meth(JNIEnv *env, jobject ml
#define MLSTATICFUNC(meth)  JNICALL Java_com_wolfram_jlink_NativeLink_##meth(JNIEnv *env, jclass clz

#if JDEBUGLEVEL > 0
#  define DEBUGSTR1(x) DEBUGSTR(x)
#else
#  define DEBUGSTR1(x)
#endif

#if JDEBUGLEVEL > 1
#  define DEBUGSTR2(x) DEBUGSTR(x)
#else
#  define DEBUGSTR2(x)
#endif

/* DEBUGSTR should never appear in the code, only DEBUGSTR1 or DEBUGSTR2 */
#ifdef WINDOWS_MATHLINK
#  include <windows.h>
#  define DEBUGSTR(x) MessageBox(NULL, x, "MathLinkJavaLibrary Debug", MB_OK);
#else
#  define DEBUGSTR(x)
#endif

/* Must be in sync with Java code. */
#define TYPE_BOOLEAN	-1
#define TYPE_BYTE		-2
#define TYPE_CHAR		-3
#define TYPE_SHORT		-4
#define TYPE_INT		-5
#define TYPE_LONG		-6
#define TYPE_FLOAT		-7
#define TYPE_DOUBLE		-8
#define TYPE_STRING		-9

#define MLE_LINK_IS_NULL		MLEUSER
#define MLE_MEMORY				MLEUSER + 1
#define MLE_ARRAY_TOO_SHALLOW	MLEUSER + 2   /* Requested array is deeper than actual */

#ifdef _64BIT
#  define JLONG_FROM_PTR(x) ((jlong) (x))
#  define PTR_FROM_JLONG(x) ((void*) (x))
#else
#  define JLONG_FROM_PTR(x) ((jlong) (int) (x))
#  define PTR_FROM_JLONG(x) ((void*) (int) (x))
#endif

static jobject MakeArrayN(JNIEnv* env, int type, int depth, int* dims, int curDepth, int lenInFinalDim, const void* startAddr);
static jobject MakeArray1(JNIEnv* env, int type, int len, const void* startAddr);

/* The structure stored in the link's UserData area. Used to support yield/msg functions. */
struct cookie {
	MLYieldFunctionObject yielder;
	MLMessageHandlerObject msgHandler;
	JavaVM* jvm;
	jobject ml;
	jmethodID yieldMID;
	jmethodID msgMID;
	int useJavaYielder;
	int useJavaMsgHandler;
};

enum ctype {
	kMsg,
	kYield
};
typedef enum ctype CallbackType;

static int initEnvironment(void);
static void destroyEnvironment(void);
static void setupUserData(MLINK link, MLEnvironment env, JNIEnv* jniEnv, jobject ml);
MLMDECL(void, msg_handler, (MLINK, int, int));
MLYDECL(devyield_result, yield_func, (MLINK, MLYieldParameters));
void setupCallback(JNIEnv* env, jlong link, CallbackType type, int revoke);


/* gWasTerminated is like the MLDone variable in mprep-generated installable C programs. It communicates from the
   messagehandler to the yielder that a terminate request has arrived from Mathematica.
*/
int gWasTerminated = 0;

/* All links share the same env. */
MLEnvironment gMLEnv = (MLEnvironment) 0;
/* Ref count for gMLEnv variable. */
int gEnvUseCount = 0;


/********************************  Library Management  ************************************/

/* These functions only called by 1.2 and later VMs. */

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *vm, void *reserved) {

	return JNI_VERSION_1_2;
}

JNIEXPORT void JNICALL JNI_OnUnload(JavaVM *vm, void *reserved) {

	/* Last chance to call MLEnd() and free MathLink resources (e.g., bug 59200).
	   In normal use, the ref-counting mechanism for gMLEnv will have already
	   called MLEnd() after the last link was closed. But we do it here in case
	   there are circumstances where this unload func is called but some links
	   still exist that haven't been closed. Just about the only way I can
	   imagine that is if a programmer didn't manually a link and its finalizer
	   wasn't called, but this unload func _was_ called. Don't know if that's
	   possible, though.
	*/
	if (gMLEnv != (MLEnvironment) 0) {
		MLEnd(gMLEnv);
		gMLEnv = (MLEnvironment) 0;
	}
}


/******************************  MathLink Functions  ********************************/

JNIEXPORT void MLSTATICFUNC(MLInitialize)) {

	initEnvironment();
}


JNIEXPORT jlong MLFUNC(MLOpenString), jstring cmdLine, jobjectArray errMsgOut) {

	const char* utfString = (*env)->GetStringUTFChars(env, cmdLine, NULL);
	if (utfString == NULL) {
		return JLONG_FROM_PTR(0);
	} else {
		int err;
		MLINK link;
		DEBUGSTR1(utfString)
		if (!initEnvironment())
			return 0;
		link = MLOpenString(gMLEnv, utfString, &err);
		if (link != NULL) {
			gEnvUseCount++;
			setupUserData(link, gMLEnv, env, ml);
		} else if (err != MLEOK) {
			jstring errMsg = (*env)->NewStringUTF(env, MLErrorString(gMLEnv, err));
			(*env)->SetObjectArrayElement(env, errMsgOut, 0, errMsg);
		}
		(*env)->ReleaseStringUTFChars(env, cmdLine, utfString);
		return JLONG_FROM_PTR(link);
	}
}


JNIEXPORT jlong MLFUNC(MLOpen), jint argc, jobjectArray argv, jobjectArray errMsgOut) {

	int err;
	int i;
	const char *c_argv[32];  /* More than enough for any argv. */
	MLINK link;

	int len = (*env)->GetArrayLength(env, argv);
	for (i = 0; i < len && i < argc && i < 32; i++) {
		jobject obj = (*env)->GetObjectArrayElement(env, argv, i);
		if (obj == NULL) {
			return JLONG_FROM_PTR(0);
		}
		c_argv[i] = (*env)->GetStringUTFChars(env, (jstring) obj, NULL);
		if (c_argv[i] == NULL) {
			/* Yes, we may fail to call RELEASESTRINGUTFCHARS here... */
			return JLONG_FROM_PTR(0);
		}
	}
	if (!initEnvironment())
		return 0;
	link = MLOpenInEnv(gMLEnv, i, (char **) c_argv, &err);
	if (link != NULL) {
		gEnvUseCount++;
		setupUserData(link, gMLEnv, env, ml);
	} else if (err != MLEOK) {
		jstring errMsg = (*env)->NewStringUTF(env, MLErrorString(gMLEnv, err));
		(*env)->SetObjectArrayElement(env, errMsgOut, 0, errMsg);
	}
	while (--i >= 0) {
		(*env)->ReleaseStringUTFChars(env, (jstring) (*env)->GetObjectArrayElement(env, argv, i), c_argv[i]);
	}
	return JLONG_FROM_PTR(link);
}


JNIEXPORT jlong MLSTATICFUNC(MLLoopbackOpen), jobjectArray errMsgOut) {

	MLINK link;
	int err;

	if (!initEnvironment())
		return 0;
	link = MLLoopbackOpen(gMLEnv, &err);
	if (link != NULL) {
		gEnvUseCount++;
		/* Don't call setupUserData. No yield function for loopbacks. */
		MLSetUserData(link, NULL, NULL);
	} else if (err != MLEOK) {
		jstring errMsg = (*env)->NewStringUTF(env, MLErrorString(gMLEnv, err));
		(*env)->SetObjectArrayElement(env, errMsgOut, 0, errMsg);
	}
	return JLONG_FROM_PTR(link);
}


JNIEXPORT void MLSTATICFUNC(MLSetEnvIDString), jstring id) {

	const char* chars = (*env)->GetStringUTFChars(env, id, NULL);
	if (chars != NULL) {
		MLSetEnvIDString(gMLEnv, chars);
		(*env)->ReleaseStringUTFChars(env, id, chars);
	}
}


JNIEXPORT jstring MLSTATICFUNC(MLGetLinkedEnvIDString), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

    jstring result;
	if (mlink == 0) {
        result = (*env)->NewStringUTF(env, "");
		DEBUGSTR1(" link is 0 in MLGetLinkedEnvIDString")
	} else {
        const char* s;
		MLGetLinkedEnvIDString(mlink, &s);
        result = (*env)->NewStringUTF(env, s);
		MLReleaseEnvIDString(mlink, s);
	}
	return result;
}


JNIEXPORT void MLSTATICFUNC(MLConnect), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLConnect")
	} else {
		MLConnect(mlink);
	}
}


JNIEXPORT void MLSTATICFUNC(MLClose), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLClose")
	} else {
		struct cookie* c = (struct cookie*) MLUserData(mlink, NULL);
		MLSetUserData(mlink, NULL, NULL);
		if (c != NULL) {
			/* A C-side yieldfunction and its accoutrements were set. Clean it up. */
			MLSetYieldFunction(mlink, (MLYieldFunctionObject) NULL);
			MLSetMessageHandler(mlink, (MLMessageHandlerObject) NULL);
			MLDestroyYieldFunction(c->yielder);
			MLDestroyMessageHandler(c->msgHandler);
			if (c->ml != NULL) (*env)->DeleteGlobalRef(env, c->ml); /* A Java-side handler for yield or msg was set. */
			free(c);
		}
		MLClose(mlink);
		gEnvUseCount--;
		if (gEnvUseCount == 0)
			destroyEnvironment();
	}
}


JNIEXPORT jstring MLSTATICFUNC(MLName), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	const char *s;
	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLErrorMessage")
		s = "";
	} else {
		s = MLName(mlink);
	}
	return (*env)->NewStringUTF(env, s);
}


JNIEXPORT void MLFUNC(MLSetYieldFunction), jlong link, jboolean revoke) {

	setupCallback(env, link, kYield, revoke);
}


JNIEXPORT void MLFUNC(MLSetMessageHandler), jlong link) {

	setupCallback(env, link, kMsg, 0);
}


JNIEXPORT void MLSTATICFUNC(MLNewPacket), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLNewPacket")
	} else {
		MLNewPacket(mlink);
	}
}


JNIEXPORT void MLSTATICFUNC(MLEndPacket), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLEndPacket")
	} else {
		MLEndPacket(mlink);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLNextPacket), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLNextPacket")
		return ILLEGALPKT;
	} else {
		return MLNextPacket(mlink);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLError), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLError")
		return MLE_LINK_IS_NULL;
	} else {
		return MLError(mlink);
	}
}


JNIEXPORT jstring MLSTATICFUNC(MLErrorMessage), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	const char *s;
	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLErrorMessage")
		s = "";
	} else {
		s = MLErrorMessage(mlink);
	}
	return (*env)->NewStringUTF(env, s);
}


JNIEXPORT jboolean MLSTATICFUNC(MLClearError), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLClearError")
		return (jboolean) 0;
	} else {
		return (jboolean) MLClearError(mlink);
	}
}


JNIEXPORT void MLSTATICFUNC(MLSetError), jlong link, jint err) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLSetError")
	} else {
		MLSetError(mlink, err);
	}
}


JNIEXPORT jboolean MLSTATICFUNC(MLReady), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLReady")
		return (jboolean) 0;
	} else {
		return (jboolean) MLReady(mlink);
	}
}


JNIEXPORT void MLSTATICFUNC(MLFlush), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLFlush")
	} else {
		MLFlush(mlink);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLGetNext), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetNext")
		return (jint) MLTKERR;
	} else {
		return (jint) MLGetNext(mlink);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLGetType), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetType")
		return (jint) MLTKERR;
	} else {
		return (jint) MLGetType(mlink);
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutNext), jlong link, jint type) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutNext")
	} else {
		MLPutNext(mlink, (int) type);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLGetArgCount), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetArgCount")
		return (jint) 0;
	} else {
		int argc;
		if (MLGetArgCount(mlink, &argc) != 0) {
			return (jint) argc;
		} else {
			return (jint) 0;
		}
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutArgCount), jlong link, jint cnt) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutArgCount")
	} else {
		MLPutArgCount(mlink, (int) cnt);
	}
}


JNIEXPORT jstring MLSTATICFUNC(MLGetString), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetString")
		return (*env)->NewString(env, NULL, 0);
	} else {
		const unsigned short *s;
		int len;
		jstring str;
		if (MLGetUCS2String(mlink, &s, &len) == 0) {
			DEBUGSTR1(" MLGetUnicodeString failed")
			return (*env)->NewString(env, NULL, 0);
		}
		str = (*env)->NewString(env, s, len);
		MLReleaseUCS2String(mlink, s, len);
		return str;
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutString), jlong link, jstring s) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutString")
	} else if (s == NULL) {
		MLPutSymbol(mlink, "Null");
	} else {
		const jchar* chars = (*env)->GetStringChars(env, s, NULL);
		MLPutUCS2String(mlink, chars, (*env)->GetStringLength(env, s));
		(*env)->ReleaseStringChars(env, s, chars);
	}
}


JNIEXPORT jbyteArray MLSTATICFUNC(MLGetByteString), jlong link, jbyte missing) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	jbyteArray res = NULL;
	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetByteString")
	} else {
		const unsigned char *s;
		int len;
		if (MLGetByteString(mlink, &s, &len, missing) == 0) {
			DEBUGSTR1(" MLGetByteString failed")
		} else {
			res = (*env)->NewByteArray(env, len);
			if (res != NULL) {
				(*env)->SetByteArrayRegion(env, res, 0, len, (jbyte*)s);
			}
			MLReleaseByteString(mlink, s, len);
		}
	}
	return res;
}


JNIEXPORT void MLSTATICFUNC(MLPutByteString), jlong link, jbyteArray data, jint len) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutByteString")
	} else if (data == NULL) {
		DEBUGSTR1(" data is null in MLPutByteString")
	} else {
		jbyte *c_data = (*env)->GetByteArrayElements(env, data, NULL);
		if (c_data == NULL) {
			DEBUGSTR1(" mem failure in MLPutByteString")
			MLSetError(mlink, MLE_MEMORY);
			return;
		}
		MLPutByteString(mlink, (unsigned char*)c_data, len);
		(*env)->ReleaseByteArrayElements(env, data, c_data, JNI_ABORT);
	}
}


JNIEXPORT jstring MLSTATICFUNC(MLGetSymbol), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetSymbol")
		return NULL;
	} else {
		const unsigned short *s;
		int len;
		jstring str;
		if (MLGetUCS2Symbol(mlink, &s, &len) == 0) {
			DEBUGSTR1(" MLGetSymbol failed")
			return NULL;
		}
		str = (*env)->NewString(env, s, len);
		MLReleaseUCS2Symbol(mlink, s, len);
		if (str == NULL) {
			DEBUGSTR1(" mem failure in MLGetSymbol")
			MLSetError(mlink, MLE_MEMORY);
		}
		return str;
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutSymbol), jlong link, jstring s) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutSymbol")
	} else if (s == NULL) {
		MLPutSymbol(mlink, "Null");
	} else {
		const jchar* chars = (*env)->GetStringChars(env, s, NULL);
		MLPutUCS2Symbol(mlink, chars, (*env)->GetStringLength(env, s));
		(*env)->ReleaseStringChars(env, s, chars);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLGetInteger), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetInteger")
		return (jint) 0;
	} else {
		int i;
		if (MLGetInteger(mlink, &i) != 0) {
			return (jint) i;
		} else {
			return (jint) 0;
		}
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutInteger), jlong link, jint i) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutInteger")
	} else {
		MLPutInteger(mlink, (int) i);
	}
}


JNIEXPORT jdouble MLSTATICFUNC(MLGetDouble), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetDouble")
		return (jdouble) 0.0;
	} else {
		double d;
		if (MLGetDouble(mlink, &d) != 0) {
			return (jdouble) d;
		} else {
			return (jdouble) 0.0;
		}
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutDouble), jlong link, jdouble d) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutDouble")
	} else {
		MLPutDouble(mlink, (double) d);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLCheckFunction), jlong link, jstring s) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	/* This needs to be Unicode-ified.... */
	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLCheckFunction")
		return (jint) 0;
	} else if (s == NULL) {
		DEBUGSTR1(" string is null in MLCheckFunction")
		return (jint) 0;
	} else {
		const char *f = (*env)->GetStringUTFChars(env, s, NULL);
		if (f == NULL) {
			MLSetError(mlink, MLE_MEMORY);
			return (jint) 0;
		} else {
			long argCount = 0;
			MLCheckFunction(mlink, f, &argCount);
			(*env)->ReleaseStringUTFChars(env, s, f);
			return (jint) argCount;
		}
	}
}


JNIEXPORT jint MLSTATICFUNC(MLCheckFunctionWithArgCount), jlong link, jstring s, jint argc) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	/* This needs to be Unicode-ified.... */
	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLCheckFunctionWithArgCount")
		return (jint) 0;
	} else if (s == NULL) {
		DEBUGSTR1(" string is null in MLCheckFunctionWithArgCount")
		return (jint) 0;
	} else {
		const char *f = (*env)->GetStringUTFChars(env, s, NULL);
		if (f == NULL) {
			MLSetError(mlink, MLE_MEMORY);
			return (jint) 0;
		} else {
			long argCount = (long) argc;
			MLCheckFunctionWithArgCount(mlink, f, &argCount);
			(*env)->ReleaseStringUTFChars(env, s, f);
			return (jint) argCount;
		}
	}
}


JNIEXPORT jbyteArray MLSTATICFUNC(MLGetData), jlong link, jint len) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	jbyteArray res = NULL;
	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetData")
	} else {
		int cnt;
		char *buf = malloc(len);
		if (buf == NULL) {
			DEBUGSTR1(" Out of memory in MLGetData")
			MLSetError(mlink, MLE_MEMORY);
		} else if (!MLGetData(mlink, buf, len, &cnt)) {
			DEBUGSTR1(" MLGetData failed")
		} else {
			res = (*env)->NewByteArray(env, cnt);
			if (res != NULL) {
				(*env)->SetByteArrayRegion(env, res, 0, cnt, (jbyte*)buf);
			}
		}
		if (buf) free(buf);
	}
	return res;
}


JNIEXPORT void MLSTATICFUNC(MLPutData), jlong link, jbyteArray data, jint len) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutData")
	} else if (data == NULL) {
		DEBUGSTR1(" data is null in MLPutData")
	} else {
		jbyte *c_data = (*env)->GetByteArrayElements(env, data, NULL);
		if (c_data == NULL) {
			DEBUGSTR1(" mem failure in MLPutData")
			MLSetError(mlink, MLE_MEMORY);
			return;
		}
		MLPutData(mlink, (const char*)c_data, len);
		(*env)->ReleaseByteArrayElements(env, data, c_data, JNI_ABORT);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLBytesToGet), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLBytesToGet")
		return (jint) 0;
	} else {
		int i;
		if (MLBytesToGet(mlink, &i) != 0) {
			return (jint) i;
		} else {
			return (jint) 0;
		}
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutSize), jlong link, jint len) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutSize")
	} else {
		MLPutSize(mlink, len);
	}
}


JNIEXPORT jint MLSTATICFUNC(MLBytesToPut), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLBytesToPut")
		return (jint) 0;
	} else {
		int i;
		if (MLBytesToPut(mlink, &i) != 0) {
			return (jint) i;
		} else {
			return (jint) 0;
		}
	}
}


/* Maximum depth is 5 (required by C code; must be enforced by the calling Java code). */
JNIEXPORT jobject MLSTATICFUNC(MLGetArray), jlong link, jint type, jint depth, jobjectArray headsArray) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	int i;
	int *dims;
	char **heads;
	int actualDepth, lenInLastDimension;
	jobject retval;
	void *data;
	int res;

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetArray")
		return (jobject) NULL;
	}

	switch (type) {
		case TYPE_BYTE:
		case TYPE_SHORT:
			res = MLGetInteger16Array(mlink, (short**) &data, &dims, &heads, &actualDepth);
			break;
		case TYPE_CHAR:
		case TYPE_INT:
			res = MLGetInteger32Array(mlink, (int**) &data, &dims, &heads, &actualDepth);
			break;
		case TYPE_FLOAT:
			res = MLGetReal32Array(mlink, (float**) &data, &dims, &heads, &actualDepth);
			break;
		case TYPE_DOUBLE:
			res = MLGetReal64Array(mlink, (double**) &data, &dims, &heads, &actualDepth);
			break;
		default:
			/* Don't have to worry about proper cleanup here since this is only to catch bugs during development. */
			DEBUGSTR1(" Bad type in MLGetArray")
			return (jobject) NULL;
	}

	if (res == 0)
		return (jobject) NULL;

	if (headsArray != NULL) {
		int headsArrayLen = (*env)->GetArrayLength(env, headsArray);
		for (i = 0; i < actualDepth && i < headsArrayLen; i++)
			(*env)->SetObjectArrayElement(env, headsArray, i, (*env)->NewStringUTF(env, heads[i]));
	}

	if (actualDepth >= depth) {
		lenInLastDimension = dims[depth-1];
		for (i = depth; i < actualDepth; i++) {
			lenInLastDimension *= dims[i];
		}
		retval = MakeArrayN(env, type, depth, dims, 0, lenInLastDimension, data);
	} else {
		/* It is an error to request an array deeper than what is actually there. */
		MLSetError(mlink, MLE_ARRAY_TOO_SHALLOW);
		retval = (jobject) NULL;
	}

	switch (type) {
		case TYPE_BYTE:
		case TYPE_SHORT:
			MLReleaseInteger16Array(mlink, (short*)data, dims, heads, actualDepth);
			break;
		case TYPE_CHAR:
		case TYPE_INT:
			MLReleaseInteger32Array(mlink, (int*)data, dims, heads, actualDepth);
			break;
		case TYPE_FLOAT:
			MLReleaseReal32Array(mlink, (float*)data, dims, heads, actualDepth);
			break;
		case TYPE_DOUBLE:
			MLReleaseReal64Array(mlink, (double*)data, dims, heads, actualDepth);
			break;
	}

	return retval;
}


/* Never called unless we already know that the JNI native size of the primitive array can be handled by an MLPutXXXArray
   raw MathLink call. Thus, we never have to worry about manually sending an array element-by-element.
*/
JNIEXPORT void MLSTATICFUNC(MLPutArrayFlat), jlong link, jint type, jobject data, jobjectArray heads, jintArray dims) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	int depth;
	jint *temp_dims;
	int c_dims[5];
	char head1[256], head2[256], head3[256], head4[256], head5[256];
	char *c_heads[5];
	int usesHeads;
	int i;

	c_heads[0] = head1;
	c_heads[1] = head2;
	c_heads[2] = head3;
	c_heads[3] = head4;
	c_heads[4] = head5;

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutArrayFlat")
		return;
	} else if (data == NULL) {
		DEBUGSTR1(" data is null in MLPutArrayFlat")
		return;
	}

	depth = (*env)->GetArrayLength(env, dims);
	temp_dims = (*env)->GetIntArrayElements(env, dims, NULL);
	if (temp_dims == NULL) {
		DEBUGSTR1(" mem failure in MLPutArrayFlat")
		return;
	}
	for (i = 0; i < depth && i < 5; i++)
		c_dims[i] = temp_dims[i];  /* Converting from jint to long. */
	(*env)->ReleaseIntArrayElements(env, dims, temp_dims, JNI_ABORT);

	usesHeads = heads != (jobjectArray) NULL;
	if (usesHeads) {
		for (i = 0; i < (*env)->GetArrayLength(env, heads); i++) {
			jstring s = (jstring)((*env)->GetObjectArrayElement(env, heads, i));
			char *p = (char*) (*env)->GetStringUTFChars(env, s, NULL);
			strncpy(c_heads[i], p, 255);
			c_heads[i][255] = 0;
			(*env)->ReleaseStringUTFChars(env, s, p);
		}
	}

	switch (type) {
		case TYPE_BYTE:  /* Byte was converted to short in Java code, because MLPutByteArray won't work--it converts to unsigned. */
		case TYPE_SHORT: {
			jshort *c_data = (*env)->GetShortArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArrayFlat")
				break;
			}
			MLPutInteger16Array(mlink, (short*)c_data, c_dims, usesHeads ? c_heads : NULL, depth);
			(*env)->ReleaseShortArrayElements(env, data, c_data, JNI_ABORT);
			break;
		}
		case TYPE_CHAR:  /* Char was converted to int in Java code, because MLPutShortIntegerArray won't work--it converts to signed. */
		case TYPE_INT: {
			jint *c_data = (*env)->GetIntArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArrayFlat")
				break;
			}
			MLPutInteger32Array(mlink, (int*)c_data, c_dims, usesHeads ? c_heads : NULL, depth);
			(*env)->ReleaseIntArrayElements(env, data, c_data, JNI_ABORT);
			break;
		}
		case TYPE_LONG: {
			jlong *c_data = (*env)->GetLongArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				break;
			}
			MLPutInteger64Array(mlink, (mlint64*)c_data, c_dims, usesHeads ? c_heads : NULL, depth);
			(*env)->ReleaseLongArrayElements(env, data, c_data, JNI_ABORT);
			break;
		}
		case TYPE_FLOAT: {
			jfloat *c_data = (*env)->GetFloatArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArrayFlat")
				break;
			}
			MLPutReal32Array(mlink, (float*)c_data, c_dims, usesHeads ? c_heads : NULL, depth);
			(*env)->ReleaseFloatArrayElements(env, data, c_data, JNI_ABORT);
			break;
		}
		case TYPE_DOUBLE: {
			jdouble *c_data = (*env)->GetDoubleArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArrayFlat")
				break;
			}
			MLPutReal64Array(mlink, (double*)c_data, c_dims, usesHeads ? c_heads : NULL, depth);
			(*env)->ReleaseDoubleArrayElements(env, data, c_data, JNI_ABORT);
			break;
		}
		default:
			break;
	}
	return;
}


JNIEXPORT void MLSTATICFUNC(MLPutArray), jlong link, jint type, jobject data, jstring head) {

	/* Changed in J/Link 1.1. Now it is only passed 1-D arrays. Slicing of arrays is now done in Java code. */

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	int i;
	char c_head[256]; /* Limit of 256 chars on symbol names for head at deepest level of array. */
	char *head_ptr = c_head;
	int len;

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutArray")
		return;
	} else if (data == NULL) {
		DEBUGSTR1(" data is null in MLPutArray")
		return;
	}

	if (head != NULL) {
		char *p = (char*) (*env)->GetStringUTFChars(env, head, NULL);
		strncpy(c_head, p == NULL ? "List" : p, 255);
		c_head[255] = 0;
		(*env)->ReleaseStringUTFChars(env, head, p);
	} else {
		c_head[0] = 'L'; c_head[1] = 'i'; c_head[2] = 's'; c_head[3] = 't'; c_head[4] = 0;
	}

	len = (*env)->GetArrayLength(env, data);
	if (len == 0) {
		/* MLPutXXXArray dunctions in the MathLink C API cannot handle arrays of length 0, so we do these
		   differently. All arrays with a 0 anywhere in their dims are routed in Java so that they will go through here
		   (never MLPutArrayFlat()).
		*/
		MLPutFunction(mlink, c_head, 0);
		return;
	}
	switch (type) {
		case TYPE_BOOLEAN: {
			jboolean *c_data = (*env)->GetBooleanArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			MLPutFunction(mlink, c_head, len);
			for (i = 0; i < len; i++) {
				MLPutSymbol(mlink, c_data[i] ? "True" : "False");
			}
			(*env)->ReleaseBooleanArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_BYTE: {
			short* shortData, *p;
			jbyte* jp;
			jbyte *c_data = (*env)->GetByteArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			/* If we use MLPutByteArray, we get conversion to 0..255 range. Thus, we use alternate means. */
			shortData = (short*) malloc(len * sizeof(short));
			if (shortData != NULL) {
				for (p = shortData, jp = c_data; p - shortData < len; )
					*p++ = *jp++;
				MLPutInteger16Array(mlink, shortData, &len, &head_ptr, 1);
				free(shortData);
			} else {
				MLPutFunction(mlink, c_head, len);
				for (i = 0; i < len; i++) {
					MLPutInteger(mlink, (int) c_data[i]);
				}
			}
			(*env)->ReleaseByteArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_CHAR: {
			jchar *c_data = (*env)->GetCharArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			/* If we use MLPutShortIntegerArray, we get conversion to -32768..32767 range. Thus, we put the array piecemeal.
			   I could try the trick used above for byte, but that would cost more memory for a modest speedup. Not too concerned
			   about speed with the rare type char.
			*/
			MLPutFunction(mlink, c_head, len);
			for (i = 0; i < len; i++) {
				MLPutInteger(mlink, (int) c_data[i]);
			}
			(*env)->ReleaseCharArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_SHORT: {
			jshort *c_data = (*env)->GetShortArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			MLPutInteger16Array(mlink, (short*)c_data, &len, &head_ptr, 1);
			(*env)->ReleaseShortArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_INT: {
			jint *c_data = (*env)->GetIntArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			MLPutInteger32Array(mlink, (int*)c_data, &len, &head_ptr, 1);
			(*env)->ReleaseIntArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_LONG: {
			jlong *c_data = (*env)->GetLongArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			MLPutInteger64Array(mlink, (mlint64*)c_data, &len, &head_ptr, 1);
			(*env)->ReleaseLongArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_FLOAT: {
			jfloat *c_data = (*env)->GetFloatArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			MLPutReal32Array(mlink, (float*)c_data, &len, &head_ptr, 1);
			(*env)->ReleaseFloatArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_DOUBLE: {
			jdouble *c_data = (*env)->GetDoubleArrayElements(env, data, NULL);
			if (c_data == NULL) {
				DEBUGSTR1(" mem failure in MLPutArray")
				return;
			}
			MLPutReal64Array(mlink, (double*)c_data, &len, &head_ptr, 1);
			(*env)->ReleaseDoubleArrayElements(env, data, c_data, JNI_ABORT);
			return;
		}
		case TYPE_STRING: {
			MLPutFunction(mlink, c_head, len);
			for (i = 0; i < len; i++) {
				jstring s = (jstring)((*env)->GetObjectArrayElement(env, data, i));
				if (s != NULL) {
					const jchar* chars = (*env)->GetStringChars(env, s, NULL);
					MLPutUCS2String(mlink, chars, (*env)->GetStringLength(env, s));
					(*env)->ReleaseStringChars(env, s, chars);
					(*env)->DeleteLocalRef(env, s);
				} else {
					MLPutSymbol(mlink, "Null");
				}
			}
			return;
		}
		default:
			DEBUGSTR1(" Bad type in MLPutArray")
			break;
	}
}


JNIEXPORT jboolean MLSTATICFUNC(nativeSizesMatch), jint type) {

	switch (type) {
		case TYPE_BYTE:  /* byte arrays are are expanded to short in the Java code, so the test is the same. */
		case TYPE_SHORT:
			return (jboolean) (sizeof(jshort) == sizeof(short));
		case TYPE_CHAR:  /* char arrays are are expanded to int in the Java code, so the test is the same. */
		case TYPE_INT:
			return (jboolean) (sizeof(jint) == sizeof(int) || sizeof(jint) == sizeof(long));
		case TYPE_LONG:
			return (jboolean) (sizeof(jlong) == sizeof(long) || sizeof(jlong) == sizeof(int));
		case TYPE_FLOAT:
			return (jboolean) (sizeof(jfloat) == sizeof(float));
		case TYPE_DOUBLE:
			return (jboolean) (sizeof(jdouble) == sizeof(double) || sizeof(jdouble) == sizeof(float));
		default:
			return (jboolean) 0; /* Satisfy the compiler only; code should never reach here. */
	}
}


JNIEXPORT void MLSTATICFUNC(MLTransferExpression), jlong dest, jlong source) {

	if (PTR_FROM_JLONG(source) == 0 || PTR_FROM_JLONG(dest) == 0) {
		DEBUGSTR1(" link or source is null in MLTransferExpression")
	} else {
		MLTransferExpression((MLINK) PTR_FROM_JLONG(dest), (MLINK) PTR_FROM_JLONG(source));
	}
}


JNIEXPORT void MLSTATICFUNC(MLTransferToEndOfLoopbackLink), jlong dest, jlong source) {

	if (PTR_FROM_JLONG(source) == 0 || PTR_FROM_JLONG(dest) == 0) {
		DEBUGSTR1(" link or source is null in MLTransferToEndOfLoopbackLink")
	} else {
		MLTransferToEndOfLoopbackLink((MLINK) PTR_FROM_JLONG(dest), (MLINK) PTR_FROM_JLONG(source));
	}
}


JNIEXPORT jint MLSTATICFUNC(MLGetMessage), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLGetMessage")
		return (jint) 0;
	} else {
		int m1 = 0, m2 = 0;
		MLGetMessage(mlink, &m1, &m2);
		return (jint) m1;
	}
}


JNIEXPORT void MLSTATICFUNC(MLPutMessage), jlong link, jint msg) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLPutMessage")
	} else {
		MLPutMessage(mlink, (int) msg);
	}
}


JNIEXPORT jboolean MLSTATICFUNC(MLMessageReady), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLMessageReady")
		return (jboolean) 0;
	} else {
		return (jboolean) MLMessageReady(mlink);
	}
}


JNIEXPORT jlong MLSTATICFUNC(MLCreateMark), jlong link) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLCreateMark")
		return JLONG_FROM_PTR(0);
	} else {
		return JLONG_FROM_PTR(MLCreateMark(mlink));
	}
}


JNIEXPORT void MLSTATICFUNC(MLSeekMark), jlong link, jlong mark) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLSeekMark")
	} else {
		MLSeekMark(mlink, (MLINKMark) PTR_FROM_JLONG(mark), 0);
	}
}


JNIEXPORT void MLSTATICFUNC(MLDestroyMark), jlong link, jlong mark) {

	MLINK mlink = (MLINK) PTR_FROM_JLONG(link);

	if (mlink == 0) {
		DEBUGSTR1(" link is 0 in MLDestroyMark")
	} else {
		MLDestroyMark(mlink, (MLINKMark) PTR_FROM_JLONG(mark));
	}
}


/***************************  Environment init/deinit  *****************************/

static int initEnvironment(void) {

    MLEnvironmentParameter p;
    if (gMLEnv == (MLEnvironment) 0) {
#ifdef WINDOWS_MATHLINK
		gMLEnv = MLBegin(0);
#else
        p = MLNewParameters(MLREVISION, MLAPIREVISION);
        /* Prevent collision of MathLink's SIGSEGV handler with the one Java installs. See bug 94033. */
        MLDoNotHandleSignalParameter(p, SIGSEGV);
        gMLEnv = MLBegin(p);	
#endif
    }
	return gMLEnv != (MLEnvironment) 0;
}

static void destroyEnvironment(void) {

	if (gMLEnv != (MLEnvironment) 0) {
		MLEnd(gMLEnv);
		gMLEnv = (MLEnvironment) 0;
	}
}

/****************************  Yielding and Messages  *********************************/

static void setupUserData(MLINK mlp, MLEnvironment mlEnv, JNIEnv* env, jobject ml) {

	JavaVM *jvm = NULL;
	struct cookie* cookie = malloc(sizeof(struct cookie));
	jclass mlCls;

	MLYieldFunctionObject yielder = MLCreateYieldFunction(mlEnv, (MLYieldFunctionType) yield_func, 0);
	MLMessageHandlerObject handler = MLCreateMessageHandler(mlEnv, (MLMessageHandlerType) msg_handler, 0);
	MLSetYieldFunction(mlp, yielder);
	MLSetMessageHandler(mlp, handler);

	if ((*env)->GetJavaVM(env, &jvm) != 0 || jvm == NULL) {
		DEBUGSTR1("GetJavaVM failed")
		return;
	}

	mlCls = (*env)->GetObjectClass(env, ml);

	cookie->yielder = yielder;
	cookie->msgHandler = handler;
	cookie->jvm = jvm;
	cookie->ml = (*env)->NewGlobalRef(env, ml);
	cookie->msgMID = (*env)->GetMethodID(env, mlCls, "nativeMessageCallback", "(II)V");
	cookie->yieldMID = (*env)->GetMethodID(env, mlCls, "nativeYielderCallback", "(Z)Z");
	cookie->useJavaYielder = 0;
	cookie->useJavaMsgHandler = 0;
	MLSetUserData(mlp, (char *)cookie, NULL);
}

void setupCallback(JNIEnv* env, jlong link, CallbackType type, int revoke) {

	MLINK mlp = PTR_FROM_JLONG(link);
	struct cookie* cookie;

	if (mlp == 0) {
		DEBUGSTR1(" link is 0 in setupCallback")
		return;
	}

	cookie = (struct cookie*) MLUserData(mlp, NULL);

	if (cookie == NULL) {
		/* Should never happen. Would require a user to attempt this operation on a loopback link. */
		DEBUGSTR1(" cookie is NULL in setupCallback")
		return;
	}

	if (type == kYield)
		cookie->useJavaYielder = revoke ? 0 : 1;
	else
		cookie->useJavaMsgHandler = revoke ? 0 : 1;
}


MLMDEFN(void, msg_handler, (MLINK mlp, int message, int n)) {

	int needsAttach = 1;
	JNIEnv* env;
	struct cookie* cookie = (struct cookie*) MLUserData(mlp, NULL);
	if (cookie == NULL) {
		/* Should never happen. */
		DEBUGSTR1("cookie was NULL in msg_handler")
		return;
	}

	if (message == MLTerminateMessage)
		gWasTerminated = 1;

	if (!cookie->useJavaMsgHandler) {
		/* Normal. No Java-side msghandler set. */
		return;
	}

	needsAttach = (*(cookie->jvm))->GetEnv(cookie->jvm, (void**) &env, JNI_VERSION_1_2) == JNI_EDETACHED;

	if (needsAttach) {
		if ((*(cookie->jvm))->AttachCurrentThread(cookie->jvm, (void**) &env, NULL) != 0) {
			DEBUGSTR1("AttachCurrentThread in msghandler failed")
			return;
		}
	}

	/* The function being called here is nativeMessageCallback in class MathLink. */
	(*env)->CallVoidMethod(env, cookie->ml, cookie->msgMID, (jint) message, (jint) n);

	if (needsAttach)
		(*(cookie->jvm))->DetachCurrentThread(cookie->jvm);
}

MLYDEFN(devyield_result, yield_func, (MLINK mlp, MLYieldParameters yp)) {

	int needsAttach = 1;
	jboolean res = 0;
	struct cookie* cookie = (struct cookie*) MLUserData(mlp, NULL);
	JNIEnv* env;

	/* If an MLTerminateMessage has arrived, immediately back out of any read calls. */
	if (gWasTerminated)
		return 1;

	if (cookie == NULL) {
		/* Should never happen. */
		DEBUGSTR1("cookie was NULL in yieldfunction")
		return 0;
	}

	if (!cookie->useJavaYielder) {
		/* Normal. No Java-side yielder set. */
		return 0;
	}

	needsAttach = (*(cookie->jvm))->GetEnv(cookie->jvm, (void**) &env, JNI_VERSION_1_2) == JNI_EDETACHED;

	if (needsAttach) {
		if ((*(cookie->jvm))->AttachCurrentThread(cookie->jvm, (void**) &env, NULL) != 0) {
			DEBUGSTR1("AttachCurrentThread in yieldfunction failed")
			return 0;
		}
	}

	/* The function being called here is nativeYielderCallback in class MathLink. */
	res = (*env)->CallBooleanMethod(env, cookie->ml, cookie->yieldMID, 0 /* will be removed */);

	if (needsAttach)
		(*(cookie->jvm))->DetachCurrentThread(cookie->jvm);

	return (devyield_result) res;
}

/***************************************************************************************/

static jobject MakeArray1(JNIEnv* env, int type, int len, const void* startAddr) {

	int i;

	switch (type) {
		case TYPE_BYTE: {
			jbyte* a;
			jbyteArray ja = (*env)->NewByteArray(env, len);
			if (ja == NULL) {
				return (jobject) NULL;
			}
			/* Cannot use SetByteArrayRegion because we have a short*, not a char*. */
			a = (*env)->GetByteArrayElements(env, ja, NULL);
			if (a == NULL) {
				DEBUGSTR1(" GetByteArrayElements failed in makeArray1");
				return (jobject) NULL;
			}
			for (i = 0; i < len; i++) {
				a[i] = (jbyte) ((short*) startAddr)[i];
			}
			(*env)->ReleaseByteArrayElements(env, ja, a, 0);
			return (jobject) ja;
		}
		case TYPE_CHAR: {
			jchar* a;
			jcharArray ja = (*env)->NewCharArray(env, len);
			if (ja == NULL) {
				return (jobject) NULL;
			}
			/* Cannot use SetCharArrayRegion because we have an int*, not a short*. */
			a = (*env)->GetCharArrayElements(env, ja, NULL);
			if (a == NULL) {
				DEBUGSTR1(" GetCharArrayElements failed in makeArray1");
				return (jobject) NULL;
			}
			for (i = 0; i < len; i++) {
				a[i] = (jchar) ((int*) startAddr)[i];
			}
			(*env)->ReleaseCharArrayElements(env, ja, a, 0);
			return (jobject) ja;
		}
		case TYPE_SHORT: {
			jshortArray ja = (*env)->NewShortArray(env, len);
			if (ja == NULL) {
				return (jobject) NULL;
			}
			(*env)->SetShortArrayRegion(env, ja, 0, len, (jshort*)startAddr);
			return (jobject) ja;
		}
		case TYPE_INT: {
			jintArray ja = (*env)->NewIntArray(env, len);
			if (ja == NULL) {
				return (jobject) NULL;
			}
			(*env)->SetIntArrayRegion(env, ja, 0, len, (jint*)startAddr);
			return (jobject) ja;
		}
		case TYPE_FLOAT: {
			jfloatArray ja = (*env)->NewFloatArray(env, len);
			if (ja == NULL) {
				return (jobject) NULL;
			}
			(*env)->SetFloatArrayRegion(env, ja, 0, len, (jfloat*)startAddr);
			return (jobject) ja;
		}
		case TYPE_DOUBLE: {
			jdoubleArray ja = (*env)->NewDoubleArray(env, len);
			if (ja == NULL) {
				return (jobject) NULL;
			}
			(*env)->SetDoubleArrayRegion(env, ja, 0, len, (jdouble*)startAddr);
			return (jobject) ja;
		}
		default:
			return NULL;  /* Just to silence a compiler warning.*/
	}
}


static jobject MakeArrayN(JNIEnv* env, int type, int depth, int* dims, int curDepth, int lenInFinalDim, const void* startAddr) {

	jobjectArray joa;
	int i, datSize;
	char typeChar;
	char typeStr[6];  /* largest str will be [[[[ + char + 0. Accommodates a depth 5 array. */
	jclass componentClass;

	if (depth == 1)
		return MakeArray1(env, type, lenInFinalDim, startAddr);

	switch (type) {
		case TYPE_BYTE:
			typeChar = 'B';
			datSize = sizeof(short);   /* These are the sizes of the data types in the MathLink arrays we read (so, == short for TYPE_BYTE) */
			break;
		case TYPE_CHAR:
			typeChar = 'C';
			datSize = sizeof(int);
			break;
		case TYPE_SHORT:
			typeChar = 'S';
			datSize = sizeof(short);
			break;
		case TYPE_INT:
			typeChar = 'I';
			datSize = sizeof(int);
			break;
		case TYPE_FLOAT:
			typeChar = 'F';
			datSize = sizeof(float);
			break;
		case TYPE_DOUBLE:
			typeChar = 'D';
			datSize = sizeof(double);
			break;
		default:
			DEBUGSTR1(" Bad type passed to makeArrayN")
			return (jobject) NULL;
	}
	switch (depth) {
		/* case 1 already handled at start of func. */
		/* Note spaces at end; they will be overwritten by a char. */
		case 2: strcpy(typeStr, "[ "); break;
		case 3: strcpy(typeStr, "[[ "); break;
		case 4: strcpy(typeStr, "[[[ "); break;
		case 5: strcpy(typeStr, "[[[[ "); break;
	}
	typeStr[depth - 1] = typeChar;

	componentClass = (*env)->FindClass(env, typeStr);
	joa = (*env)->NewObjectArray(env, dims[curDepth], componentClass, NULL);
	(*env)->DeleteLocalRef(env, componentClass);
	if (joa == NULL) {
		DEBUGSTR1(" NewObjectArray failed in makeArrayN")
		return (jobject) NULL;
	}
	for (i = 0; i < dims[curDepth]; i++) {
		jobject jo;
		size_t jump = lenInFinalDim;
		int j;
		for (j = curDepth + 1; j < curDepth + depth - 1; j++)
			jump *= dims[j];
		jo = MakeArrayN(env, type, depth - 1, dims, curDepth + 1, lenInFinalDim, (char*)startAddr + i*jump*datSize);
		if (jo == NULL) {
			return (jobject) NULL;
		}
		(*env)->SetObjectArrayElement(env, joa, i, jo);
		(*env)->DeleteLocalRef(env, jo);
	}
	return (jobject) joa;
}


/****************************  platform-dependent  *********************************/

/* Bit of a hack. Want to minimize Java MS-DOS window after Java is launched. */

JNIEXPORT void MLSTATICFUNC(hideJavaWindow)) {

#ifdef WINDOWS_MATHLINK
	BOOL CALLBACK hideJavaWindowCallback(HWND, LPARAM);
	WNDENUMPROC callbackFunc = (WNDENUMPROC) &hideJavaWindowCallback;
	EnumWindows(callbackFunc, 0);
#endif
}

#ifdef WINDOWS_MATHLINK

BOOL CALLBACK hideJavaWindowCallback(HWND hwnd, LPARAM lParam) {
	DWORD winProcID, curProcID;
	curProcID = GetCurrentProcessId();
	GetWindowThreadProcessId(hwnd, &winProcID);
	if (curProcID == winProcID && IsWindowVisible(hwnd))
		CloseWindow(hwnd);
	return TRUE;
}

#endif


/* Need a little help from C for Mac and Windows to get Java windows to the foreground. */

JNIEXPORT void MLSTATICFUNC(macJavaLayerToFront)) {

#if defined(DARWIN_MATHLINK) || defined(X86_DARWIN_MATHLINK) || defined(X86_64_DARWIN_MATHLINK)
	ProcessSerialNumber psn;
	if (GetCurrentProcess(&psn) == noErr)
		SetFrontProcess(&psn);
#endif
}


JNIEXPORT void MLSTATICFUNC(winJavaLayerToFront), jboolean attach) {

#ifdef WINDOWS_MATHLINK
	/* We call AttachThreadInput to get around restrictions in Win 98 and later on who is allowed to set the
	   foreground window. Java can't put its window to the front since it is not the foreground app, but this
	   trick lets us pretend that our thread is the foreground thread. The attach param is true when this is
	   called before toFront() and false when it is called after.
	*/
	DWORD foregroundThread = GetWindowThreadProcessId(GetForegroundWindow(), NULL);
	DWORD thisThread = GetCurrentThreadId();
	if (foregroundThread != thisThread)
		AttachThreadInput(foregroundThread, thisThread, attach);
#endif
}


/* Only for OSX, puts Mathematica back in foreground after JLink app launches. */
JNIEXPORT void MLSTATICFUNC(mathematicaToFront)) {

#if defined(DARWIN_MATHLINK) || defined(X86_DARWIN_MATHLINK) || defined(X86_64_DARWIN_MATHLINK)
	ProcessSerialNumber psn;
	ProcessInfoRec infoRec;
	unsigned char name[256];
	infoRec.processInfoLength = sizeof(ProcessInfoRec);
	/* ProcessInfoRec struct differs in 64-bit version of OSX. */
#if __LP64__
	infoRec.processAppRef = NULL;
#else
	infoRec.processAppSpec = NULL;
#endif
	infoRec.processName = name;
	psn.highLongOfPSN = 0;
	psn.lowLongOfPSN = kNoProcess;
	while (GetNextProcess(&psn) == noErr) {
		if (GetProcessInformation(&psn, &infoRec) == noErr) {
			if (infoRec.processType == 'APPL' && infoRec.processSignature == 'OMEG') {
				SetFrontProcess(&psn);
				return;
			}
		}
	}
#endif
}


JNIEXPORT jlong MLSTATICFUNC(getNativeWindowHandle), jobject windowObj, jstring javaHomePath) {

#if defined(WINDOWS_MATHLINK)
    JAWT awt;
    JAWT_DrawingSurface* ds;
    JAWT_DrawingSurfaceInfo* dsi;
    JAWT_Win32DrawingSurfaceInfo* dsi_win;
    jint lock;
	jlong hwnd = -1;

	/* Dynamically load jawt.dll and find the JAWT_GetAWT entry point.
	   Bynamic loading instead of linking against jawt.lib avoids fatal
       errors that have occurred in certain Java configurations where
       jawt.dll cannot be found when JLinkNativeLibrary loads (the code
       below will find it, though).
   */
	if (hJawtLib == NULL || getAWTproc == NULL) {
		/* Get OS version. On NT and later, treat path as Unicode. */
		OSVERSIONINFO verInfo;
		verInfo.dwOSVersionInfoSize = sizeof(OSVERSIONINFO);
		GetVersionEx(&verInfo);
		if (verInfo.dwMajorVersion > 4 || verInfo.dwPlatformId == VER_PLATFORM_WIN32_NT) {
 			wchar_t buf[1024] = {0};  /* Ensure all 0 chars for string operations below. */
			const jchar* unicodePathStr = (*env)->GetStringChars(env, javaHomePath, NULL);
			int len = (*env)->GetStringLength(env, javaHomePath);
			wcsncpy(buf, unicodePathStr, len);
			wcscat(buf, L"\\bin\\jawt.dll");
			(*env)->ReleaseStringChars(env, javaHomePath, unicodePathStr);
			hJawtLib = LoadLibraryW(buf);
		} else {
 			char buf[1024];
			const char* pathStr = (*env)->GetStringUTFChars(env, javaHomePath, NULL);
	 		strcpy(buf, pathStr);
			strcat(buf, "\\bin\\jawt.dll");
			(*env)->ReleaseStringUTFChars(env, javaHomePath, pathStr);
			hJawtLib = LoadLibrary(buf);
		}
		if (hJawtLib == NULL)
			return -11;
		getAWTproc = (GET_AWT_PROC) GetProcAddress(hJawtLib, "_JAWT_GetAWT@8");
		if (getAWTproc == NULL)
			return -12;
	}

	/* Taken from http://java.sun.com/j2se/1.3/docs/guide/awt/AWT_Native_Interface.html */
    awt.version = JAWT_VERSION_1_4;
    if ((*getAWTproc)(env, &awt) == JNI_FALSE)
        return -13;
    ds = awt.GetDrawingSurface(env, windowObj);
    if (ds == NULL)
        return -1;
    lock = ds->Lock(ds);
    if ((lock & JAWT_LOCK_ERROR) != 0) {
        awt.FreeDrawingSurface(ds);
        return -1;
    }
    dsi = ds->GetDrawingSurfaceInfo(ds);
    if (dsi == NULL) {
        ds->Unlock(ds);
        awt.FreeDrawingSurface(ds);
        return -1;
    }
    dsi_win = (JAWT_Win32DrawingSurfaceInfo*) dsi->platformInfo;
    if(dsi_win != NULL)
		hwnd = (jlong) dsi_win->hwnd;

    ds->FreeDrawingSurfaceInfo(dsi);
    ds->Unlock(ds);
    awt.FreeDrawingSurface(ds);

    return hwnd;
#else
	/* Note that althuogh this is currently the correct implementation
	   for non-Windows platforms, this function is actually only called
	   under Windows.
	*/
	return -1;
#endif
}


/* Added as a convenience function for webMathematica. Not documented, not supported. */
JNIEXPORT jint MLSTATICFUNC(killProcess), jlong pid) {

#ifdef WINDOWS_MATHLINK
	HANDLE phandle = OpenProcess(PROCESS_TERMINATE, FALSE, (int) pid);
	if (phandle == NULL)
		return -1;
	if (!TerminateProcess(phandle, 1))
		return GetLastError();
	CloseHandle(phandle);
	return 0;
#elif defined(UNIX_MATHLINK)
	if (kill((pid_t) pid, SIGKILL) == 0)
		return 0;
	else
		return errno;
#else
	/* Not supported on classic MacOS. */
	return -1;
#endif
}


JNIEXPORT void MLSTATICFUNC(appToFront), jlong pid) {

#ifdef WINDOWS_MATHLINK
	BOOL CALLBACK appMainWindowToFrontCallback(HWND, LPARAM);
	WNDENUMPROC callbackFunc = (WNDENUMPROC) &appMainWindowToFrontCallback;

	/* We call AttachThreadInput to get around restrictions in Win 98 and later on who is allowed to set the
	   foreground window. Java can't put its window to the front since it is not the foreground app, but this
	   trick lets us pretend that our thread is the foreground thread.
	*/
	DWORD foregroundThread = GetWindowThreadProcessId((HWND) pid, NULL);
	DWORD thisThread = GetCurrentThreadId();
	if (foregroundThread != thisThread)
		AttachThreadInput(foregroundThread, thisThread, TRUE);

	EnumWindows(callbackFunc, (LPARAM) pid);

	if (foregroundThread != thisThread)
		AttachThreadInput(foregroundThread, thisThread, FALSE);
#endif

#if 0  /* DARWIN_MATHLINK, X86_DARWIN_MATHLINK */
	/* This is not a real implementation, just some code that is pasted
	 * here temporarily to remind me of some of the Carbon functions for
	 * working with processes. IIRC, the value given by $NotebookPRocessID on
	 * Darwin doesn't look like a PSN as used in this code.
	*/
	ProcessSerialNumber psn;
	ProcessInfoRec infoRec;
	char name[256];
	infoRec.processInfoLength = sizeof(ProcessInfoRec);
	infoRec.processAppSpec = NULL;
	infoRec.processName = name;
	psn.highLongOfPSN = 0;
	psn.lowLongOfPSN = kNoProcess;
	while (GetNextProcess(&psn) == noErr) {
		if (GetProcessInformation(&psn, &infoRec) == noErr) {
			if (infoRec.processType == 'APPL' && infoRec.processSignature == 'OMEG') {
				SetFrontProcess(&psn);
				return;
			}
		}
	}
#endif

}

#ifdef WINDOWS_MATHLINK

BOOL CALLBACK appMainWindowToFrontCallback(HWND hwnd, LPARAM lParam) {
	DWORD winProcID;
	GetWindowThreadProcessId(hwnd, &winProcID);
	/* lParam is the procID of the app we want to bring to the foreground. */
	if ((DWORD)lParam == winProcID && IsWindowVisible(hwnd))
		SetForegroundWindow(hwnd);
	return TRUE;
}

#endif

